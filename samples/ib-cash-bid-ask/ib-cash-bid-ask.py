#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
###############################################################################

# When setting the parameter "what='ASK'" the quoted price for Ask will be used from the incoming messages (field 2) instead of the default Bid price (field 1).

# BID: <tickPrice tickerId=16777217, field=1, price=1.11582, canAutoExecute=1>
# ASK: <tickPrice tickerId=16777219, field=2, price=1.11583, canAutoExecute=1>

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import datetime


class St(bt.Strategy):
    def logdata(self):
        txt = []
        txt.append('{}'.format(len(self)))
        txt.append('{}'.format(self.data.datetime.datetime(0).isoformat()))
        txt.append(' open BID: ' + '{}'.format(self.datas[0].open[0]))
        txt.append(' open ASK: ' + '{}'.format(self.datas[1].open[0]))
        txt.append(' high BID: ' + '{}'.format(self.datas[0].high[0]))
        txt.append(' high ASK: ' + '{}'.format(self.datas[1].high[0]))
        txt.append(' low BID: ' + '{}'.format(self.datas[0].low[0]))
        txt.append(' low ASK: ' + '{}'.format(self.datas[1].low[0]))
        txt.append(' close BID: ' + '{}'.format(self.datas[0].close[0]))
        txt.append(' close ASK: ' + '{}'.format(self.datas[1].close[0]))
        txt.append(' volume: ' + '{:.2f}'.format(self.data.volume[0]))
        print(','.join(txt))

    data_live = False

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if self.datas[0]._laststatus == self.datas[0].LIVE and self.datas[1]._laststatus == self.datas[1].LIVE:
            self.data_live = True

    # def notify_order(self, order):
    #     if order.status == order.Completed:
    #         buysell = 'BUY ' if order.isbuy() else 'SELL'
    #         txt = '{} {}@{}'.format(buysell, order.executed.size,
    #                                 order.executed.price)
    #         print(txt)

    # bought = 0
    # sold = 0

    def next(self):
        self.logdata()
        if not self.data_live:
            return

        # if not self.bought:
        #     self.bought = len(self)  # keep entry bar
        #     self.buy()
        # elif not self.sold:
        #     if len(self) == (self.bought + 3):
        #         self.sell()


ib_symbol = 'EUR.USD-CASH-IDEALPRO'
compression = 5

def run(args=None):
    cerebro = bt.Cerebro(stdstats=False)
    store = bt.stores.IBStore(port=7497,
                              # _debug=True
                              )

    data0 = store.getdata(dataname=ib_symbol,
                          timeframe=bt.TimeFrame.Ticks,
                          )
    cerebro.resampledata(data0,
                         timeframe=bt.TimeFrame.Seconds,
                         compression=compression
                         )

    data1 = store.getdata(dataname=ib_symbol,
                          timeframe=bt.TimeFrame.Ticks,
                          what='ASK'
                          )
    cerebro.resampledata(data1,
                         timeframe=bt.TimeFrame.Seconds,
                         compression=compression
                         )

    cerebro.broker = store.getbroker()
    cerebro.addstrategy(St)
    cerebro.run()


if __name__ == '__main__':
    run()
