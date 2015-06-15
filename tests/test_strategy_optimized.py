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

CHKVALUES = [
    u'14525.80', u'14525.80', u'15408.20', u'15408.20', u'14763.90',
    u'14763.90', u'14763.90', u'14763.90', u'14763.90', u'14763.90',
    u'14763.90', u'14763.90', u'14763.90', u'14763.90', u'13187.10',
    u'13187.10', u'13187.10', u'13684.40', u'13684.40', u'13684.40',
    u'13684.40', u'13684.40', u'13684.40', u'13656.10', u'13656.10',
    u'13656.10', u'13656.10', u'12988.10', u'12988.10', u'12988.10',
    u'12988.10', u'12988.10', u'12988.10', u'12988.10', u'12988.10',
    u'12988.10', u'12988.10', u'12988.10', u'12988.10', u'12988.10'
]

CHKCASH = [
    u'13525.80', u'13525.80', u'14408.20', u'14408.20', u'13763.90',
    u'13763.90', u'13763.90', u'13763.90', u'13763.90', u'13763.90',
    u'13763.90', u'13763.90', u'13763.90', u'13763.90', u'12187.10',
    u'12187.10', u'12187.10', u'12684.40', u'12684.40', u'12684.40',
    u'12684.40', u'12684.40', u'12684.40', u'12656.10', u'12656.10',
    u'12656.10', u'12656.10', u'11988.10', u'11988.10', u'11988.10',
    u'11988.10', u'11988.10', u'11988.10', u'11988.10', u'11988.10',
    u'11988.10', u'11988.10', u'11988.10', u'11988.10', u'11988.10'
]

_chkvalues = []
_chkcash = []


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

    def stop(self):
        tused = time.clock() - self.tstart
        if self.p.printdata:
            self.log('Time used: %s' % str(tused))
            self.log('Final portfolio value: %.2f' % self.broker.getvalue())
            self.log('-------------------------')

        value = '%.2f' % self.broker.getvalue()
        _chkvalues.append(value)

        cash = '%.2f' % self.broker.getcash()
        _chkcash.append(cash)


    def next(self):
        if self.orderid:
            # if an order is active, no new orders are allowed
            return

        if not self.position.size:
            if self.cross > 0.0:
                self.orderid = self.buy()

        elif self.cross < 0.0:
            self.orderid = self.close()


chkdatas = 1


def test_run(main=False):
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    testcommon.runtest(datas,
                       TestStrategy,
                       optimize=True,
                       period=xrange(5, 45),
                       printdata=main,
                       printops=main,
                       plot=False)

    if not main:
        assert CHKVALUES == _chkvalues
        assert CHKCASH == _chkcash

    else:
        print(_chkvalues)
        print(_chkcash)


if __name__ == '__main__':
    test_run(main=True)
