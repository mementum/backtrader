#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################
import testbase

import datetime
import os.path
import time
import sys

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btindicators


class TestStrategy(bt.Strategy):

    def __init__(self):
        self.ohlc = self.datas[0]
        self.close = self.ohlc.close

        if True:
            btindicators.MovingAverageSimple(self.datas[0], period=30)
            pass
        else:
            self.stocslow = btindicators.StochasticSlow(self.datas[0])
            self.macd2 = btindicators.MACDHisto2(self.datas[0])
            btindicators.AverageTrueRange(self.datas[0])
            btindicators.MACDHisto(self.datas[0])
            btindicators.MACD(self.datas[0])
            btindicators.MACDHistogram(self.datas[0])
            btindicators.MovingAverageSimple(self.datas[0], period=30)
            btindicators.MovingAverageSimple(self.ind1, period=10)
            btindicators.MovingAverageExponential(self.datas[0], period=30)
            btindicators.MovingAverageWeighted(self.datas[0], period=30)
            btindicators.RSI(self.datas[0])
            btindicators.RSI(self.datas[0], matype=btindicators.MATypes.Exponential)
            btindicators.StochasticFast(self.datas[0])
            btindicators.StochasticFull(self.datas[0])
            btindicators.StochasticSlow(self.datas[0])

        print '--------------------------------------------------'
        for indicator in self._indicators:
            print '%s period %d' % (indicator.__class__.__name__, indicator._minperiod)

    def start(self):
        self.tcstart = time.clock()

    def next(self):
        pass

    def stop(self):
        tused = time.clock() - self.tcstart
        print '--------------------------------------------------'
        print 'Time used', tused

        for indicator in self._indicators:
            print '--------------------------------------------------'
            print '%s period %d' % (indicator.__class__.__name__, indicator._minperiod)
            basetxt = '%5d: %s - Close %.2f - Indicator' \
                      % (len(self.ohlc), self.ohlc.datetime[0].isoformat(), self.close[0])

            for i in xrange(indicator.size()):
                basetxt += ' %.2f' % (indicator.lines[i][0],)

            print basetxt

cerebro = bt.Cerebro(preload=True, runonce=True)

# The datas are in a subdirectory of the samples. Need to find where the script is
# because it could have been called from anywhere
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = os.path.join(modpath, '../samples/datas/yahoo/oracle-1995-2014.csv')
data = bt.feeds.YahooFinanceCSVData(dataname=datapath, reversed=True)

cerebro.adddata(data)
cerebro.addstrategy(TestStrategy)
cerebro.run()
