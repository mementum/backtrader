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

from backtrader import Strategy, BrokerBack, Cerebro
from backtrader.feeds import YahooFinanceCSV
from backtrader.indicators import MovingAverageSimple


class TestStrategy(Strategy):
    params = (('period', 15), ('stake', 10), ('printdata', True))

    def __init__(self):
        self.data = self.env.datas[0]
        self.dataclose = self.data.close
        self.sma = MovingAverageSimple(self.env.datas[0], period=self.params.period)

    def start(self):
        self.tstart = datetime.datetime.now()

    def ordernotify(self, order):
        if order.status == order.Completed:
            if order.order == order.OrderBuy:
                print '%s, BUY , %.2f' % (order.dtcomplete.isoformat(), order.price)
            elif order.order == order.OrderSell:
                print '%s, SELL, %.2f' % (order.dtcomplete.isoformat(), order.price)

    def next(self):
        if self.params.printdata:
            print '%s, Close, %f, Sma, %f' % (self.data.date[0].isoformat(), self.dataclose[0], self.sma[0][0])

        if not self.position(self.data):
            if self.dataclose[0] > self.sma[0][0]:
                self.buy(self.data, size=self.params.stake)

        elif self.dataclose[0] < self.sma[0][0]:
            self.sell(self.data, size=self.params.stake)

    def stop(self):
        tused = datetime.datetime.now() - self.tstart
        print 'Time used:', str(tused)
        print 'Final portfolio value: %.2f' % self.getbroker().getvalue()

cerebro = Cerebro()
cerebro.addbroker(BrokerBack(cash=1000))
# cerebro.addfeed(YahooFinanceCSV('./datas/yahoo/oracle-2000.csv'))
cerebro.addfeed(YahooFinanceCSV('./datas/yahoo/oracle-1995-2014.csv'))
cerebro.addstrategy(TestStrategy, printdata=False)
cerebro.run()
