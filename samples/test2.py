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

from datetime import datetime

import backtrader.cerebro as btcerebro
import backtrader.feeds as btfeeds
import backtrader.indicators as btindicators
import backtrader.strategy as btstrategy


class TestStrategy(btstrategy.Strategy):
    def __init__(self, *args, **kwargs):
        self.data = self.env.datas[0]
        self.date = self.env.datas[0].datetime
        self.open = self.env.datas[0].open
        self.high = self.env.datas[0].high
        self.low = self.env.datas[0].low
        self.close = self.env.datas[0].close

    def next(self):
        if True:
            print '%5d - %s - %.2f - %.2f - %.2f - %.2f' % \
                (len(self.close),
                 self.datetime[0].isoformat(),
                 self.open[0],
                 self.high[0],
                 self.low[0],
                 self.close[0])


# feed = btfeeds.YahooFinance('ORCL', todate=datetime(2000, 1, 1), fromdate=datetime(2000, 12, 31), period='d')
# feed = btfeeds.YahooFinance('ORCL', fromdate=datetime(2000, 1, 1), todate=datetime(2000, 12, 31), period='d', savetofile='datas/yahoo/oracle-2000.csv')
feed = btfeeds.YahooFinanceCSV('./datas/yahoo/oracle-2000.csv')

cerebro = btcerebro.Cerebro()
cerebro.addfeed(feed)
cerebro.addstrategy(TestStrategy)
cerebro.run()
