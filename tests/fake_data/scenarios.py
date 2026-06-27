#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import datetime
import os

import backtrader as bt


class FakeDateTimeLine(object):
    def __getitem__(self, index):
        return 0.0

    def date(self):
        return datetime.date(2020, 1, 1)


class FakeData(object):
    _name = 'FAKE'
    datetime = FakeDateTimeLine()
    close = [100.0]
    _tz = None

    def __len__(self):
        return 0

    def num2date(self, value, tz=None, naive=True):
        return datetime.datetime(2020, 1, 1)


class FakeCommInfo(object):
    def getvaluesize(self, size, price):
        return abs(size) * price

    def profitandloss(self, size, price, newprice):
        return size * (newprice - price)

    def getoperationcost(self, size, price):
        return abs(size) * price

    def getcommission(self, size, price):
        return abs(size) * price * 0.001


def execute_order(position, order, size, price, partial):
    pprice_orig = position.price
    psize, pprice, opened, closed = position.update(size, price)

    comminfo = order.comminfo
    closedvalue = comminfo.getoperationcost(closed, pprice_orig)
    closedcomm = comminfo.getcommission(closed, price)
    openedvalue = comminfo.getoperationcost(opened, price)
    openedcomm = comminfo.getcommission(opened, price)
    pnl = comminfo.profitandloss(-closed, pprice_orig, price)
    margin = comminfo.getvaluesize(size, price)

    order.execute(order.data.datetime[0],
                  size, price,
                  closed, closedvalue, closedcomm,
                  opened, openedvalue, openedcomm,
                  margin, pnl,
                  psize, pprice)

    if partial:
        order.partial()
    else:
        order.completed()


def scenario_position():
    pos = bt.Position(size=10, price=100.0)
    assert pos.update(size=5, price=110.0) == (15, 103.33333333333333, 5, 0)
    assert pos.update(size=-8, price=120.0) == (7, 103.33333333333333, 0, -8)
    assert pos.update(size=-12, price=90.0) == (-5, 90.0, -5, -7)
    return {'size': pos.size, 'price': pos.price}


def scenario_order_pending():
    position = bt.Position()
    order = bt.BuyOrder(data=FakeData(),
                        size=100, price=1.0,
                        exectype=bt.Order.Market,
                        simulated=True)
    order.addcomminfo(FakeCommInfo())

    execute_order(position, order, 10, 1.0, True)
    execute_order(position, order, 20, 1.1, True)
    clone = order.clone()
    pending = clone.executed.getpending()
    assert [(bit.size, bit.price) for bit in pending] == [(10, 1.0), (20, 1.1)]

    execute_order(position, order, 30, 1.2, True)
    execute_order(position, order, 40, 1.3, False)
    clone = order.clone()
    pending = clone.executed.getpending()
    assert [(bit.size, bit.price) for bit in pending] == [(30, 1.2), (40, 1.3)]
    assert order.status == bt.Order.Completed
    return {'status': order.getstatusname(), 'pending': len(pending)}


def scenario_trade():
    trade = bt.Trade(data=FakeData(), historyon=True)
    order = bt.BuyOrder(data=FakeData(),
                        size=0, price=1.0,
                        exectype=bt.Order.Market,
                        simulated=True)
    comminfo = FakeCommInfo()

    trade.update(order=order, size=10, price=10.0, value=100.0,
                 commission=1.0, pnl=0.0, comminfo=comminfo)
    assert trade.isopen and not trade.isclosed

    trade.update(order=order, size=-4, price=12.0, value=48.0,
                 commission=0.5, pnl=0.0, comminfo=comminfo)
    assert trade.size == 6
    assert trade.pnl == 8.0

    trade.update(order=order, size=-6, price=11.0, value=66.0,
                 commission=0.5, pnl=0.0, comminfo=comminfo)
    assert trade.isclosed
    assert trade.pnl == 14.0
    assert len(trade.history) == 3
    return {'pnl': trade.pnl, 'pnlcomm': trade.pnlcomm}


def scenario_comminfo():
    stock = bt.CommissionInfo(commission=0.01)
    futures = bt.CommissionInfo(commission=2.0, margin=1000.0, mult=10.0)
    pos = bt.Position(size=3, price=100.0)

    assert stock.getoperationcost(size=3, price=100.0) == 300.0
    assert stock.getcommission(size=3, price=100.0) == 3.0
    assert stock.profitandloss(pos.size, pos.price, 105.0) == 15.0

    assert futures.getoperationcost(size=3, price=100.0) == 3000.0
    assert futures.getcommission(size=3, price=100.0) == 6.0
    assert futures.profitandloss(pos.size, pos.price, 105.0) == 150.0
    return {'stock_commission': 3.0, 'futures_commission': 6.0}


class FakeBrokerForSizer(object):
    def __init__(self):
        self.comminfo = bt.CommInfoBase(commission=0.0)

    def getcommissioninfo(self, data):
        return self.comminfo

    def getcash(self):
        return 1234.0


class TenSizer(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        assert cash == 1234.0
        return 10 if isbuy else 5


def scenario_sizer_and_broker():
    class Data(object):
        _name = 'FAKE'

    broker = bt.BrokerBase()
    broker.setcommission(commission=0.5, name='FAKE')
    assert broker.getcommissioninfo(Data()).p.commission == 0.5

    sizer = TenSizer()
    sizer.set(strategy='strategy', broker=FakeBrokerForSizer())
    assert sizer.getsizing(data=Data(), isbuy=True) == 10
    assert sizer.getsizing(data=Data(), isbuy=False) == 5
    return {'buy_size': 10, 'sell_size': 5}


class FakeLine(object):
    def __init__(self, value):
        self.value = value

    def __getitem__(self, ago):
        return self.value


def scenario_fillers():
    class Data(object):
        high = FakeLine(101.0)
        low = FakeLine(100.0)
        volume = FakeLine(100)

    class Executed(object):
        remsize = 80

    class Order(object):
        data = Data()
        executed = Executed()

    assert bt.broker.fillers.FixedSize(size=10)(Order(), 100.0, 0) == 10
    assert bt.broker.fillers.FixedBarPerc(perc=50.0)(Order(), 100.0, 0) == 50.0
    assert bt.broker.fillers.BarPointPerc(minmov=0.5, perc=50.0)(
        Order(), 100.5, 0) == 16.0
    return {'fixed': 10, 'bar_perc': 50.0, 'point_perc': 16.0}


class BuyThenCloseStrategy(bt.Strategy):
    def __init__(self):
        self.orders_seen = 0
        self.trades_seen = 0

    def next(self):
        if len(self) == 1:
            self.buy(size=1)
        elif len(self) == 4 and self.position:
            self.close()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Partial]:
            self.orders_seen += 1

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades_seen += 1


def scenario_cerebro_run():
    data_path = os.path.join(os.path.dirname(__file__), 'tiny-ohlcv.csv')
    data = bt.feeds.GenericCSVData(
        dataname=data_path,
        dtformat='%Y-%m-%d',
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=6,
        headers=True)

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(10000.0)
    cerebro.adddata(data)
    cerebro.addstrategy(BuyThenCloseStrategy)
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)
    cerebro.addanalyzer(bt.analyzers.PeriodStats, _name='periodstats')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.FundValue)

    strategies = cerebro.run()
    strategy = strategies[0]
    periodstats = strategy.analyzers.periodstats.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()

    assert strategy.orders_seen >= 2
    assert strategy.trades_seen == 1
    assert 'average' in periodstats
    assert trades.total.closed == 1
    return {
        'final_value': round(cerebro.broker.getvalue(), 2),
        'closed_trades': trades.total.closed,
    }


def run_all():
    scenarios = [
        ('position', scenario_position),
        ('order_pending', scenario_order_pending),
        ('trade', scenario_trade),
        ('comminfo', scenario_comminfo),
        ('sizer_and_broker', scenario_sizer_and_broker),
        ('fillers', scenario_fillers),
        ('cerebro_run', scenario_cerebro_run),
    ]

    results = {}
    for name, func in scenarios:
        results[name] = func()

    for name in sorted(results):
        print('{}: {}'.format(name, results[name]))
    print('fake data scenarios ok')


if __name__ == '__main__':
    run_all()
