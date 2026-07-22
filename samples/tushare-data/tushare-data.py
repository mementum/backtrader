#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""使用 Tushare Pro 下载 A 股日线，并转换为 Backtrader 数据格式。

用法：
    export TUSHARE_PROXY_TOKEN='你的代理 token'
    .venv/bin/python samples/tushare-data/tushare-data.py \
        --symbol 600519 --fromdate 2023-01-01 --todate 2024-12-31
"""

from __future__ import absolute_import, division, print_function

import argparse
import os.path
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKTRADER_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
sys.path.insert(0, BACKTRADER_ROOT)
sys.path.insert(0, WORKSPACE_ROOT)

import pandas as pd

import backtrader as bt
from quant_research_v1.tushare_client import TushareClient


def normalize_symbol(symbol):
    """把 6 位 A 股代码转换成 Tushare 的交易所后缀格式。"""
    symbol = symbol.strip().upper()
    if '.' in symbol:
        code, exchange = symbol.split('.', 1)
        if len(code) != 6 or exchange not in ('SH', 'SZ', 'BJ'):
            raise ValueError('无效股票代码: {}'.format(symbol))
        return symbol

    if len(symbol) != 6 or not symbol.isdigit():
        raise ValueError('股票代码应为 6 位数字，如 600519')

    if symbol.startswith(('4', '8', '9')):
        exchange = 'BJ'
    elif symbol.startswith(('5', '6')):
        exchange = 'SH'
    else:
        exchange = 'SZ'
    return '{}.{}'.format(symbol, exchange)


def normalize_date(value):
    """校验 YYYY-MM-DD 日期并转换成 Tushare 所需的 YYYYMMDD。"""
    try:
        return pd.Timestamp(value).strftime('%Y%m%d')
    except (TypeError, ValueError):
        raise ValueError('无效日期: {}，请使用 YYYY-MM-DD'.format(value))


def to_backtrader_frame(frame, symbol):
    """把 Tushare 的倒序行情转换为 Backtrader 需要的升序 OHLCV。"""
    if frame is None or frame.empty:
        raise RuntimeError('未获取到 {} 的数据，请检查代码、日期和接口权限'.format(symbol))

    required = {'trade_date', 'open', 'high', 'low', 'close', 'vol'}
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError('Tushare 返回数据缺少字段: {}'.format(
            ', '.join(sorted(missing))))

    result = frame.rename(columns={
        'trade_date': 'date',
        'vol': 'volume',
    }).copy()
    result['date'] = pd.to_datetime(result['date'], format='%Y%m%d')
    result = result.set_index('date').sort_index()
    result.index.name = 'datetime'
    return result[['open', 'high', 'low', 'close', 'volume']].astype(float)


def fetch_stock(client, symbol, fromdate, todate, adjust='qfq'):
    """下载日线；adjust 可取 qfq、hfq 或 none。"""
    ts_code = normalize_symbol(symbol)
    start_date = normalize_date(fromdate)
    end_date = normalize_date(todate)
    if start_date > end_date:
        raise ValueError('起始日期不能晚于结束日期')

    if adjust == 'none':
        frame = client.query(
            'daily', use_cache=False, ts_code=ts_code,
            start_date=start_date, end_date=end_date)
    else:
        frame = client.pro_bar(
            use_cache=False,
            ts_code=ts_code,
            adj=adjust,
            start_date=start_date,
            end_date=end_date,
        )
    return to_backtrader_frame(frame, ts_code)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='用 Tushare Pro 下载 A 股日线数据')
    parser.add_argument('--symbol', default='600519',
                        help='股票代码，如 600519 或 600519.SH')
    parser.add_argument('--fromdate', default='2023-01-01')
    parser.add_argument('--todate', default='2024-12-31')
    parser.add_argument('--adjust', choices=('qfq', 'hfq', 'none'),
                        default='qfq', help='前复权、后复权或不复权')
    parser.add_argument('--output', help='可选的 CSV 输出路径')
    return parser.parse_args(pargs)


def run(pargs=None):
    args = parse_args(pargs)
    client = TushareClient.from_env()

    symbol = normalize_symbol(args.symbol)
    print('正在从 Tushare 拉取 {} 日线（{}）...'.format(symbol, args.adjust))
    frame = fetch_stock(
        client, symbol, args.fromdate, args.todate, args.adjust)
    print('获取 {} 根 K 线（{} ~ {}）'.format(
        len(frame), frame.index[0].date(), frame.index[-1].date()))
    print(frame.tail())

    # 这里得到的 data 可直接交给 cerebro.adddata(data)。
    data = bt.feeds.PandasData(dataname=frame, name=symbol)
    print('已转换为 Backtrader PandasData: {}'.format(data._name))

    if args.output:
        output = os.path.abspath(os.path.expanduser(args.output))
        os.makedirs(os.path.dirname(output), exist_ok=True)
        frame.to_csv(output, encoding='utf-8-sig')
        print('CSV 已保存到 {}'.format(output))


if __name__ == '__main__':
    run()
