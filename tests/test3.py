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

        self.setpositionsizer(bt.PosSizerFix(stake=self.params.stake))

    def start(self):
        self.tstart = tclock()

    def ordernotify(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return # Await further notifications

        if order.status == bt.Order.Completed:
            if isinstance(order, bt.BuyOrder):
                print '%s, BUY , %.2f' % (order.executed.dt.isoformat(), order.executed.price)
            else: # elif isinstance(order, SellOrder):
                print '%s, SELL, %.2f' % (order.executed.dt.isoformat(), order.executed.price)
        elif order.status in [bt.Order.Expired, bt.Order.Canceled]:
            pass # Do nothing for expired orders

        # Allow new orders
        self.orderid = None

    def next(self):
        if self.params.printdata:
            print '%s, Open, High, Low, Close, %.2f, %.2f, %.2f, %.2f, Sma, %f' % \
                (self.data.datetime[0].isoformat(),
                 self.data.open[0], self.data.high[0], self.data.low[0], self.dataclose[0],
                 self.sma[0][0])

        if self.orderid:
            # if an order is active, no new orders are allowed
            return

        position = self.getposition(self.data)
        if not position.size:
            if self.dataclose[0] > self.sma[0][0]:
                valid = self.data.datetime[0] + self.expiry
                price = self.dataclose[0]
                if self.params.exectype == bt.Order.Limit:
                    price *= self.params.atlimitperc
                print '%s, BUY CREATE , %.2f' % (self.data.datetime[0].isoformat(), price)
                self.orderid = self.buy(exectype=self.params.exectype, price=price, valid=valid)

        elif self.dataclose[0] < self.sma[0][0]:
            print '%s, SELL CREATE , %.2f' % (self.data.datetime[0].isoformat(), self.dataclose[0])
            self.orderid = self.sell(exectype=bt.Order.Market)

    def stop(self):
        tused = tclock() - self.tstart
        print 'Time used:', str(tused)
        print 'Final portfolio value: %.2f' % self.getbroker().getvalue()


cerebro = bt.Cerebro(preload=True)
data = btfeeds.YahooFinanceCSVData(dataname='./datas/yahoo/oracle-2000.csv', reversed=True)
# data = btfeeds.YahooFinanceCSVData(dataname='./datas/yahoo/oracle-1995-2014.csv', reversed=True)
cerebro.adddata(data)

broker = bt.BrokerBack(cash=1000.0)
# broker.setcommissioninfo(commission=0.0005)
cerebro.addbroker(broker)

cerebro.addstrategy(TestStrategy, printdata=False,
                    maperiod=15, exectype=bt.Order.Limit, atlimitperc=0.80, expiredays=7)
cerebro.run()
