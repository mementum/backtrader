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

from backtrader import BrokerBack, Cerebro, Order, Strategy
from backtrader.feeds import YahooFinanceCSV
from backtrader.indicators import MovingAverageSimple


class TestStrategy(Strategy):
    params = (
        ('maperiod', 15),
        ('stake', 10),
        ('exectype', Order.Market),
        ('atlimitperc', 1.0),
        ('expiredays', 10),
        ('printdata', True),
    )

    def __init__(self):
        self.data = self.datas[0]
        self.dataclose = self.data.close
        self.sma = MovingAverageSimple(self.data, period=self.params.maperiod)
        self.orderid = None

    def start(self):
        self.tstart = datetime.datetime.now()

    def ordernotify(self, order):
        if order.status == Order.Completed:
            if order.ordtype == order.Buy:
                print '%s, BUY , %.2f' % (order.executed.dt.isoformat(), order.executed.price)
            elif order.ordtype == order.Sell:
                print '%s, SELL, %.2f' % (order.executed.dt.isoformat(), order.executed.price)
        elif order.status == Order.Expired:
            pass # Do nothing for expired orders

        # Allow new orders
        self.orderid = None

    def next(self):
        if self.params.printdata:
            print '%s, Close, %f, Sma, %f' % (self.data.date[0].isoformat(), self.dataclose[0], self.sma[0][0])

        if self.orderid:
            # if an order is active, no new orders are allowed
            return

        if not self.position(self.data):
            if self.dataclose[0] > self.sma[0][0]:
                valid = self.data.datetime[0] + datetime.timedelta(days=self.params.expiredays)
                price = self.dataclose[0] * self.params.atlimitperc
                self.orderid = self.buy(self.data, size=self.params.stake,
                                        exectype=self.params.exectype,
                                        price=price, valid=valid)

        elif self.dataclose[0] < self.sma[0][0]:
            self.orderid = self.sell(self.data, size=self.params.stake, exectype=Order.Market)

    def stop(self):
        tused = datetime.datetime.now() - self.tstart
        print 'Time used:', str(tused)
        print 'Final portfolio value: %.2f' % self.getbroker().getvalue()


cerebro = Cerebro()
cerebro.addbroker(BrokerBack(cash=1000))
# cerebro.addfeed(YahooFinanceCSV('./datas/yahoo/oracle-2000.csv'))
cerebro.addfeed(YahooFinanceCSV('./datas/yahoo/oracle-1995-2014.csv'))
cerebro.addstrategy(TestStrategy, printdata=False, exectype=Order.Limit, atlimitperc=1.00, expiredays=5)
cerebro.run()
