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

from six.moves import xrange

import testbase

import datetime
import os.path
import time
import sys

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class OverUnderMA(bt.Indicator):
    lines = ('overunder',)
    params = (('period', 20), ('movav', btind.MovAv.Simple))
    plotinfo = dict(plotymargin=0.15,
                    plothlines=[1.0, -1.0],
                    plotyticks=[1.0, -1.0])

    def __init__(self):
        ma = self.p.movav(self.data, period=self.p.period)
        self.lines.overunder = bt.Cmp(self.data.close, ma)


class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('movav', btind.MovAv.Simple),
        ('printdata', True),
    )

    def log(self, txt, dt=None):
        if not self.p.optimize:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.p.movav(self.data, period=self.p.maperiod)
        OverUnderMA(self.data, period=self.p.maperiod, movav=self.p.movav)

    def next(self):
        if self.p.printdata:
            self.log(
                'Open, High, Low, Close, %.2f, %.2f, %.2f, %.2f, Sma, %f' %
                (self.data.open[0], self.data.high[0],
                 self.data.low[0], self.data.close[0],
                 self.sma[0])
            )


def runtest():
    cerebro = bt.Cerebro(runonce=True)

    # Datas are in a subdirectory of samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(
        modpath, '../samples/datas/yahoo/oracle-1995-2014.csv')
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        reversed=True,
        fromdate=datetime.datetime(2014, 1, 1),
        ti=datetime.datetime(2014, 12, 31),
    )

    cerebro.adddata(data)

    cerebro.addstrategy(
        TestStrategy,
        printdata=False,
        maperiod=15,
        movav=btind.MovAv.Simple)

    cerebro.run()
    cerebro.plot()


if __name__ == '__main__':
    runtest()
