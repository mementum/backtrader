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

from backtrader import Strategy, BrokerBase, BrokerTest, Cerebro
from backtrader.feeds import YahooFinanceCSV
from backtrader.indicators import MovingAverageSimple


class TestStrategy(Strategy):
    params = (('period', 15), ('stake', 10),)

    def __init__(self):
        self.data = self.env.datas[0]
        self.dataclose = self.data.lines.close
        self.sma = MovingAverageSimple(self.data, period=self.params.period)
        self.broker = self.env.brokers[0]

    def next(self):
        closeprice = self.data.close[0]
        smavalue = self.sma[0][0]
        if not self.broker.position:
            if closeprice > smavalue:
                self.broker.buy(self.data, size=self.params.stake, execution=BrokerBase.AtMarket)
                # FIXME: The actual "AtMarket" price is not the close price but the open price
                # of the next bar
                # Will be available when the broker gives information of the execution price
                print '%s - BUY  at %.2f' % (self.data.date[0].isoformat(), closeprice)

        elif closeprice < smavalue:
            self.broker.sell(self.data, size=self.params.stake, execution=BrokerBase.AtMarket)
            # FIXME: The actual "AtMarket" price is not the close price but the open price
            # of the next bar
            # Will be available when the broker gives information of the execution price
            print '%s - SELL at %.2f' % (self.data.date[0].isoformat(), closeprice)

    def stop(self):
        print 'Final portfolio value: %.2f' % self.broker.getvalue(self.data, price=self.dataclose[0])


cerebro = Cerebro()
cerebro.addbroker(BrokerTest(cash=1000))
cerebro.addfeed(YahooFinanceCSV('./datas/yahoo/oracle-2000.csv'))
cerebro.addstrategy(TestStrategy)
cerebro.run()
