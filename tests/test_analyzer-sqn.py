#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time

import testcommon

import backtrader as bt
import backtrader.indicators as btind


class TestStrategy(bt.Strategy):
    params = (
        ('period', 15),
        ('maxtrades', None),
        ('printdata', True),
        ('printops', True),
        ('stocklike', True),
    )

    def log(self, txt, dt=None, nodate=False):
        if not nodate:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))
        else:
            print('---------- %s' % (txt))

    def notify_trade(self, trade):
        if trade.isclosed:
            self.tradecount += 1

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if isinstance(order, bt.BuyOrder):
                if self.p.printops:
                    txt = 'BUY, %.2f' % order.executed.price
                    self.log(txt, order.executed.dt)
                chkprice = '%.2f' % order.executed.price
                self.buyexec.append(chkprice)
            else:  # elif isinstance(order, SellOrder):
                if self.p.printops:
                    txt = 'SELL, %.2f' % order.executed.price
                    self.log(txt, order.executed.dt)

                chkprice = '%.2f' % order.executed.price
                self.sellexec.append(chkprice)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            if self.p.printops:
                self.log('%s ,' % order.Status[order.status])

        # Allow new orders
        self.orderid = None

    def __init__(self):
        # Flag to allow new orders in the system or not
        self.orderid = None

        self.sma = btind.SMA(self.data, period=self.p.period)
        self.cross = btind.CrossOver(self.data.close, self.sma, plot=True)

    def start(self):
        if not self.p.stocklike:
            self.broker.setcommission(commission=2.0, mult=10.0, margin=1000.0)

        if self.p.printdata:
            self.log('-------------------------', nodate=True)
            self.log('Starting portfolio value: %.2f' % self.broker.getvalue(),
                     nodate=True)

        self.tstart = time.clock()

        self.buycreate = list()
        self.sellcreate = list()
        self.buyexec = list()
        self.sellexec = list()
        self.tradecount = 0

    def stop(self):
        tused = time.clock() - self.tstart
        if self.p.printdata:
            self.log('Time used: %s' % str(tused))
            self.log('Final portfolio value: %.2f' % self.broker.getvalue())
            self.log('Final cash value: %.2f' % self.broker.getcash())
            self.log('-------------------------')
        else:
            pass

    def next(self):
        if self.p.printdata:
            self.log(
                'Open, High, Low, Close, %.2f, %.2f, %.2f, %.2f, Sma, %f' %
                (self.data.open[0], self.data.high[0],
                 self.data.low[0], self.data.close[0],
                 self.sma[0]))
            self.log('Close %.2f - Sma %.2f' %
                     (self.data.close[0], self.sma[0]))

        if self.orderid:
            # if an order is active, no new orders are allowed
            return

        if not self.position.size:
            if self.p.maxtrades is None or self.tradecount < self.p.maxtrades:
                if self.cross > 0.0:
                    if self.p.printops:
                        self.log('BUY CREATE , %.2f' % self.data.close[0])

                    self.orderid = self.buy()
                    chkprice = '%.2f' % self.data.close[0]
                    self.buycreate.append(chkprice)

        elif self.cross < 0.0:
            if self.p.printops:
                self.log('SELL CREATE , %.2f' % self.data.close[0])

            self.orderid = self.close()
            chkprice = '%.2f' % self.data.close[0]
            self.sellcreate.append(chkprice)


chkdatas = 1


def test_run(main=False):
    datas = [testcommon.getdata(i) for i in range(chkdatas)]

    for maxtrades in [None, 0, 1]:
        cerebros = testcommon.runtest(datas,
                                      TestStrategy,
                                      printdata=main,
                                      stocklike=False,
                                      maxtrades=maxtrades,
                                      printops=main,
                                      plot=main,
                                      analyzer=(bt.analyzers.SQN, {}))

        for cerebro in cerebros:
            strat = cerebro.runstrats[0][0]  # no optimization, only 1
            analyzer = strat.analyzers[0]  # only 1
            analysis = analyzer.get_analysis()
            if main:
                print(analysis)
                print(str(analysis.sqn))
            else:
                if maxtrades == 0 or maxtrades == 1:
                    assert analysis.sqn == 0
                    assert analysis.trades == maxtrades
                else:
                    # Handle different precision
                    assert str(analysis.sqn)[0:14] == '0.912550316439'
                    assert str(analysis.trades) == '11'


if __name__ == '__main__':
    test_run(main=True)
