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

from time import clock as tclock

import matplotlib.pyplot as mpplt
import  matplotlib.widgets as mpwidgets

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btindicators


class TestStrategy(bt.Strategy):

    def __init__(self):
        self.ohlc = self.datas[0]
        self.close = self.ohlc.close

        if True:
            self.ind = btindicators.StochasticSlow(self.datas[0])
            # self.ind = btindicators.RSI(self.datas[0])
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
        self.tcstart = tclock()

    def next(self):
        pass

    def stop(self):
        tused = tclock() - self.tcstart
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

        if False:
            print '--------------------------------------------------'
            print 'self.macd2 macd', self.macd2.lines.macd[0]
            print 'self.macd2 signal', self.macd2.lines.signal[0]
            print 'self.macd2 histo', self.macd2.lines.histo[0]

        if False:
            print '--------------------------------------------------'
            print 'self.stocslow k', self.stocslow.lines.k[0]
            print 'self.stocslow d', self.stocslow.lines.d[0]


cerebro = bt.Cerebro(preload=True)
# data = btfeeds.YahooFinanceCSVData(dataname='./datas/yahoo/oracle-2000.csv', reversed=True)
data = btfeeds.MyCSVData(dataname='../../tmp/estx50-day-001-1991-2014.txt')
cerebro.adddata(data)
cerebro.addstrategy(TestStrategy)
cerebro.run()

fig, axis = mpplt.subplots(2, sharex=True)
dt = data.datetime.plot()
axis[0].plot(dt, data.close.plot())

for i in xrange(cerebro.runstrats[0].ind.size()):
    st = cerebro.runstrats[0].ind.lines[i].plot()
    axis[1].plot(dt, st)

fig.autofmt_xdate()
mpplt.show()
