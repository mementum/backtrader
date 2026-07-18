#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之三：真实成本 + 仓位管理 + 绩效报告
#
# 在 multidata-strategy4.py（多标的独立双均线 + 指数择时）基础上组装三块：
#
#   1. AStockCommission —— A 股真实费率：佣金万 2.5（最低 5 元）+
#      卖出单边印花税千 0.5。setcommission 表达不了不对称收费，
#      需继承 CommInfoBase 重写 _getcommission
#   2. AStockPercentSizer —— 每笔按总资产的固定百分比开仓，并按 A 股
#      规则取整到 100 股一手（不再是固定 100 股的失衡仓位）
#   3. Analyzers —— 夏普/最大回撤/SQN/交易统计，回测结束打印绩效报告，
#      不再只看期末资产一个数字
#
# 另加 --no-filter 开关关闭指数择时，方便同条件对比择时的真实价值：
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy5.py
#   .venv/bin/python samples/multidata-strategy/multidata-strategy5.py --no-filter
#   .venv/bin/python samples/multidata-strategy/multidata-strategy5.py --perc 20 --quiet
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import os
import os.path
import sys

# 东财等国内数据源直连即可，绕过系统代理（代理常导致连接失败）
os.environ['NO_PROXY'] = '*'

# 未 pip 安装 backtrader 时，直接使用仓库根目录下的源码
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import akshare as ak
import pandas as pd

import backtrader as bt


class AStockCommission(bt.CommInfoBase):
    '''A 股费率：佣金按成交额百分比双边收（有最低门槛），印花税只在卖出时收'''

    params = dict(
        commission=0.00025,   # 佣金万 2.5
        stamp_duty=0.0005,    # 印花税千 0.5（卖出单边）
        min_comm=5.0,         # 最低佣金 5 元
        stocklike=True,
        commtype=bt.CommInfoBase.COMM_PERC,
    )

    def _getcommission(self, size, price, pseudoexec):
        comm = max(abs(size) * price * self.p.commission, self.p.min_comm)
        if size < 0:  # 卖出加收印花税
            comm += abs(size) * price * self.p.stamp_duty
        return comm


class AStockPercentSizer(bt.Sizer):
    '''按总资产百分比开仓，向下取整到 100 股一手；资金不足则不下单'''

    params = dict(perc=10)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy:  # 卖出交给 close()，返回当前持仓
            return self.broker.getposition(data).size

        target = self.broker.getvalue() * self.p.perc / 100.0
        size = int(target / data.close[0] / 100) * 100
        # 至少一手，且不超过可用现金
        if size < 100 or size * data.close[0] > cash:
            return 0
        return size


class IndexFilterSmaCross(bt.Strategy):
    '''多标的独立双均线 + 可开关的指数择时（同 multidata-strategy4）

    约定：最后一个数据源是指数，只算信号不交易。
    下单不再传 size —— 交给 Sizer 决定仓位。
    '''

    params = dict(sma1=10, sma2=20, index_period=20,
                  use_filter=True, printout=True)

    def __init__(self):
        self.stocks = self.datas[:-1]
        self.index = self.datas[-1]

        self.signals = []
        for d in self.stocks:
            sma1 = bt.ind.SMA(d, period=self.p.sma1)
            sma2 = bt.ind.SMA(d, period=self.p.sma2)
            self.signals.append(bt.ind.CrossOver(sma1, sma2))

        self.index_sma = bt.ind.SMA(self.index, period=self.p.index_period)

    def log(self, txt):
        if self.p.printout:
            print('{} {}'.format(self.data.datetime.date(0), txt))

    def notify_order(self, order):
        if order.status == order.Completed:
            self.log('{} {} {}@{:.2f} 费用 {:.2f}'.format(
                order.data._name,
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price,
                order.executed.comm))
        elif not order.alive():
            self.log('{} 订单未成交: {}'.format(
                order.data._name, order.getstatusname()))

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log('{} 毛利 {:.2f} 净利 {:.2f}'.format(
                trade.data._name, trade.pnl, trade.pnlcomm))

    def next(self):
        bullish = (not self.p.use_filter or
                   self.index.close[0] > self.index_sma[0])

        if not bullish:
            for d in self.stocks:
                if self.getposition(d):
                    self.log('{} 大盘跌破均线，清仓避险'.format(d._name))
                    self.close(data=d)
            return

        for i, d in enumerate(self.stocks):
            pos = self.getposition(d)
            if not pos and self.signals[i] > 0:
                self.buy(data=d)          # size 由 Sizer 决定
            elif pos and self.signals[i] < 0:
                self.close(data=d)


def print_report(cerebro, result, args):
    '''从 analyzers 取值，打印绩效报告'''
    strat = result[0]
    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.dd.get_analysis()
    sqn = strat.analyzers.sqn.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    returns = strat.analyzers.returns.get_analysis()

    total = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)
    pnl_won = trades.get('won', {}).get('pnl', {}).get('total', 0.0)
    pnl_lost = trades.get('lost', {}).get('pnl', {}).get('total', 0.0)

    print('=' * 50)
    print('绩效报告（择时过滤: {}）'.format('开' if not args.no_filter else '关'))
    print('-' * 50)
    print('期末资产:     {:,.2f}'.format(cerebro.broker.getvalue()))
    print('总收益率:     {:.2%}'.format(returns.get('rtot', 0.0)))
    print('年化收益率:   {:.2%}'.format(returns.get('rnorm', 0.0)))
    print('最大回撤:     {:.2%}（金额 {:,.2f}）'.format(
        dd.max.drawdown / 100, dd.max.moneydown))
    print('夏普比率:     {}'.format(
        '{:.3f}'.format(sharpe['sharperatio'])
        if sharpe.get('sharperatio') is not None else 'N/A'))
    print('SQN:          {:.3f}（{} 笔）'.format(
        sqn.get('sqn', 0.0), sqn.get('trades', 0)))
    if total:
        print('胜率:         {:.1%}（{}/{}）'.format(won / total, won, total))
        if pnl_lost:
            print('盈亏比:       {:.2f}'.format(abs(pnl_won / pnl_lost)))
    print('=' * 50)


def fetch_eastmoney(symbol, fromdate, todate):
    """东财源：stock_zh_a_hist，返回中文列名"""
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period='daily',
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')
    return df.rename(columns={
        '日期': 'date',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
    })


def fetch_sina(symbol, fromdate, todate):
    """新浪源：stock_zh_a_daily，代码需带 sh/sz 前缀，列名已是英文"""
    prefix = 'sh' if symbol.startswith(('5', '6', '9')) else 'sz'
    return ak.stock_zh_a_daily(
        symbol=prefix + symbol,
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')


def normalize(df, symbol):
    """统一索引与列，转成 backtrader 可用的 DataFrame"""
    if df is None or df.empty:
        raise SystemExit('未获取到 {} 的数据，请检查代码或网络'.format(symbol))
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    return df[['open', 'high', 'low', 'close', 'volume']]


def fetch_stock(symbol, fromdate, todate):
    """个股日线（前复权）：东财失败自动降级到新浪源"""
    try:
        df = fetch_eastmoney(symbol, fromdate, todate)
    except Exception as e:
        print('{} 东财源获取失败（{}），改用新浪源...'.format(
            symbol, type(e).__name__))
        df = fetch_sina(symbol, fromdate, todate)
    return normalize(df, symbol)


def fetch_index(symbol, fromdate, todate):
    """指数日线：新浪源 stock_zh_index_daily，返回全部历史后按日期切片"""
    df = ak.stock_zh_index_daily(symbol=symbol)
    df = normalize(df, symbol)
    return df.loc[fromdate:todate]


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    # 1. A 股真实费率
    cerebro.broker.addcommissioninfo(AStockCommission())

    # 2. 按总资产百分比开仓
    cerebro.addsizer(AStockPercentSizer, perc=args.perc)

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        df = fetch_stock(symbol, args.fromdate, args.todate)
        print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
            symbol, len(df), df.index[0].date(), df.index[-1].date()))
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    # 指数必须最后加入——策略里约定 self.datas[-1] 是指数
    print('正在从 AKShare 拉取指数 {} 的日线数据...'.format(args.index))
    dfi = fetch_index(args.index, args.fromdate, args.todate)
    print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
        args.index, len(dfi), dfi.index[0].date(), dfi.index[-1].date()))
    cerebro.adddata(bt.feeds.PandasData(dataname=dfi), name=args.index)

    cerebro.addstrategy(IndexFilterSmaCross,
                        index_period=args.index_period,
                        use_filter=not args.no_filter,
                        printout=not args.quiet,
                        **(eval('dict(' + args.strat + ')')))

    # 3. 绩效分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.02,
                        annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns',
                        tann=252)

    result = cerebro.run()
    print_report(cerebro, result, args)

    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy5 - 真实费率 + 百分比仓位 + 绩效报告')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001',
                        help='A 股代码，逗号分隔，如: 600519,000001,601318')

    parser.add_argument('--index', required=False, default='sh000001',
                        help='择时用指数代码（新浪格式），如: sh000001 上证指数')

    parser.add_argument('--index-period', required=False, type=int, default=20,
                        help='指数择时均线周期')

    parser.add_argument('--no-filter', action='store_true',
                        help='关闭指数择时过滤（用于对比）')

    parser.add_argument('--perc', required=False, type=float, default=10,
                        help='每笔开仓占总资产的百分比')

    parser.add_argument('--fromdate', required=False, default='2023-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2024-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=1000000, help='初始资金')

    parser.add_argument('--strat', required=False, action='store', default='',
                        help='策略参数，如: sma1=5,sma2=30')

    parser.add_argument('--quiet', action='store_true',
                        help='不打印逐笔交易日志，只看绩效报告')

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help='绘图并可传入 kwargs，如: --plot style="candle"')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
