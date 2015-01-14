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

import collections
import datetime

import backtrader.cerebro as btcerebro
import backtrader.feeds as btfeeds
import backtrader.indicators as btindicators
import backtrader.strategy as btstrategy

feed = btfeeds.YahooFinanceCSV('./datas/yahoo/oracle-2000.csv')


class TestStrategy(btstrategy.Strategy):

    def __init__(self):
        self.ohlc = self.env.datas[0]
        self.close = self.ohlc.close

        if True:
            self.addindicator(btindicators.StochasticSlow(self.env.datas[0]))
            pass
        else:
            self.stocslow = btindicators.StochasticSlow(self.env.datas[0])
            self.macd2 = btindicators.MACDHisto2(self.env.datas[0])
            self.addindicator(btindicators.AverageTrueRange(self.env.datas[0]))
            self.addindicator(btindicators.MACDHisto(self.env.datas[0]))
            self.addindicator(btindicators.MovingAverageSimple(self.ind1, period=10))
            self.addindicator(btindicators.MovingAverageExponential(self.env.datas[0], period=30))
            self.addindicator(btindicators.MovingAverageWeighted(self.env.datas[0], period=30))
            self.addindicator(btindicators.RSI(self.env.datas[0]))
            self.addindicator(btindicators.RSI(self.env.datas[0], matype=btindicators.MATypes.Exponential))
            self.addindicator(btindicators.StochasticFast(self.env.datas[0]))
            self.addindicator(btindicators.StochasticSlow(self.env.datas[0]))

        print '--------------------------------------------------'
        for indicator in self._indicators:
            print '%s period %d' % (indicator.__class__.__name__, indicator._minperiod)

    def start(self):
        self.tstart = datetime.datetime.now()

    def next(self):
        pass

    def stop(self):
        tused = datetime.datetime.now() - self.tstart
        print '--------------------------------------------------'
        print 'Time used', tused

        for indicator in self._indicators:
            print '--------------------------------------------------'
            print '%s period %d' % (indicator.__class__.__name__, indicator._minperiod)
            basetxt = '%5d: %s - %s - Close %.2f - Indicator' \
                      % (len(self.ohlc), self.ohlc.date[0].isoformat(),
                         self.ohlc.time[0].isoformat(), self.close[0])

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


cerebro = btcerebro.Cerebro()
cerebro.addfeed(feed)
cerebro.addstrategy(TestStrategy)
cerebro.run()
