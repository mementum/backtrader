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
from time import clock as tclock

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btindicators


class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('stake', 10),
        ('exectype', bt.Order.Market),
        ('atlimitperc', 1.0),
        ('expiredays', 10),
        ('printdata', True),
    )

    def __init__(self):
        self.data = self.datas[0]
        self.dataclose = self.data.close
        self.sma = btindicators.MovingAverageSimple(self.data, period=self.params.maperiod)
        self.orderid = None
        self.expiry = datetime.timedelta(days=self.params.expiredays)

    def start(self):
        self.tstart = tclock()

    def ordernotify(self, order):
        if order.status == bt.Order.Completed:
            if isinstance(order, bt.BuyOrder):
                print '%s, BUY , %.2f' % (order.executed.dt.isoformat(), order.executed.price)
            else: # elif isinstance(order, SellOrder):
                print '%s, SELL, %.2f' % (order.executed.dt.isoformat(), order.executed.price)
        elif order.status == bt.Order.Expired:
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
                valid = self.data.datetime[0] + self.expiry
                price = self.dataclose[0] * self.params.atlimitperc
                self.orderid = self.buy(
                    self.data, size=self.params.stake, exectype=self.params.exectype, price=price, valid=valid)

        elif self.dataclose[0] < self.sma[0][0]:
            self.orderid = self.sell(self.data, size=self.params.stake, exectype=bt.Order.Market)

    def stop(self):
        tused = tclock() - self.tstart
        print 'Time used:', str(tused)
        print 'Final portfolio value: %.2f' % self.getbroker().getvalue()


cerebro = bt.Cerebro()
cerebro.addbroker(bt.BrokerBack(cash=1000))
# data = btfeeds.YahooFinanceCSVData(dataname='./datas/yahoo/oracle-2000.csv', reversed=True)
data = btfeeds.YahooFinanceCSVData(dataname='./datas/yahoo/oracle-1995-2014.csv', reversed=True)
cerebro.adddata(data)
cerebro.addstrategy(TestStrategy, printdata=False, exectype=bt.Order.Limit, atlimitperc=1.00, expiredays=2)
cerebro.run()
