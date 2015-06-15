#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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

import itertools
import time

import testcommon

import backtrader as bt
import backtrader.indicators as btind

BUYCREATE = [
    u'3641.42', u'3798.46', u'3874.61', u'3860.00', u'3843.08', u'3648.33',
    u'3526.84', u'3632.93', u'3788.96', u'3841.31', u'4045.22', u'4052.89',
]

SELLCREATE = [
    u'3763.73', u'3811.45', u'3823.11', u'3821.97', u'3837.86', u'3604.33',
    u'3562.56', u'3772.21', u'3780.18', u'3974.62', u'4048.16'
]

BUYEXEC = [
    u'3643.35', u'3801.03', u'3872.37', u'3863.57', u'3845.32', u'3656.43',
    u'3542.65', u'3639.65', u'3799.86', u'3840.20', u'4047.63', u'4052.55'
]

SELLEXEC = [
    u'3763.95', u'3811.85', u'3822.35', u'3822.57', u'3829.82', u'3598.58',
    u'3545.92', u'3766.80', u'3782.15', u'3979.73', u'4045.05'
]


class TestStrategy(bt.Strategy):
    params = (
        ('period', 15),
        ('printdata', True),
        ('printops', True),
    )

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime[0]
        dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify(self, order):
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
        self.broker.setcommission(commission=2.0, mult=10.0, margin=1000.0)
        if self.p.printdata:
            self.log('-------------------------')
            self.log('Starting portfolio value: %.2f' % self.broker.getvalue())

        self.tstart = time.clock()
        self.buy_create_idx = itertools.count()

        self.buycreate = list()
        self.sellcreate = list()
        self.buyexec = list()
        self.sellexec = list()

    def stop(self):
        tused = time.clock() - self.tstart
        if self.p.printdata:
            self.log('Time used: %s' % str(tused))
            self.log('Final portfolio value: %.2f' % self.broker.getvalue())
            self.log('-------------------------')

            print('buycreate')
            print(self.buycreate)
            print('sellcreate')
            print(self.sellcreate)
            print('buyexec')
            print(self.buyexec)
            print('sellexec')
            print(self.sellexec)

        assert '%.2f' % self.broker.getvalue() == '12795.00'
        assert '%.2f' % self.broker.getcash() == '11795.00'
        assert self.buycreate == BUYCREATE
        assert self.sellcreate == SELLCREATE
        assert self.buyexec == BUYEXEC
        assert self.sellexec == SELLEXEC

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
    testcommon.runtest(datas,
                       TestStrategy,
                       printdata=main,
                       printops=main,
                       plot=main)


if __name__ == '__main__':
    test_run(main=True)
