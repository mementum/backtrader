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
import datetime # For datetime objects
import os.path # To manage paths
import sys # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('stake', 10),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime[0]
        print '%s, %s' % (dt.isoformat(), txt)

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Set the sizer stake from the params
        self.sizer.setsizing(self.params.stake)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        bt.indicators.MovingAverageExponential(self.datas[0], period=25)
        bt.indicators.MovingAverageWeighted(self.datas[0], period=25).subplot = True
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHistogram(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.MovingAverageSmoothed(rsi, period=10)
        bt.indicators.ATR(self.datas[0]).plot = False

    def notify(self, order):
        if order.status in [order.Submitted, order.Accepted,]:
            # Buy/Sell order has been submitted/accepted to/by the broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: the broker could reject the order if not sufficient cash is available
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size %d, Price: %.2f, Cost: %.2f, Commission %.2f' % \
                         (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else: # Sell
                self.log('SELL EXECUTED, Size %d, Price: %.2f, Cost: %.2f, Commission %.2f' % \
                         (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))

                gross_pnl = (order.executed.price - self.buyprice) * order.executed.size
                net_pnl = gross_pnl - self.buycomm - order.executed.comm
                self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (gross_pnl, net_pnl))

            self.bar_executed = len(self)

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0][0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.dataclose[0] < self.sma[0][0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

# Create a cerebro entity
cerebro = bt.Cerebro()

# Add a strategy
cerebro.addstrategy(TestStrategy)

# The datas are in a subdirectory of the samples. Need to find where the script is
# because it could have been called from anywhere
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = os.path.join(modpath, './datas/yahoo/oracle-1995-2014.csv')

# Create a Data Feed
data = bt.feeds.YahooFinanceCSVData(
    dataname=datapath,
    fromdate=datetime.datetime(2000, 01, 01), # Do not pass values before this date
    todate=datetime.datetime(2000, 12, 31), # Do not pass values after this date
    reversed=True)

# Add the Data Feed to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(1000.0)

# Set the commission
cerebro.broker.setcommission(commission=0.0)

# Print out the starting conditions
print 'Starting Portfolio Value: %.2f' % cerebro.broker.getvalue()

# Run over everything
cerebro.run()

# Print out the final result
print 'Final Portfolio Value: %.2f' % cerebro.broker.getvalue()

# Plot whatever is there to be plotted
cerebro.plot()
