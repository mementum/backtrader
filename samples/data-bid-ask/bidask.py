#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import backtrader.feeds as btfeeds


class BidAskCSV(btfeeds.GenericCSVData):
    linesoverride = True  # discard usual OHLC structure
    # datetime must be present and last
    lines = ('bid', 'ask', 'datetime')
    # datetime (always 1st) and then the desired order for
    params = (
        ('dtformat', '%m/%d/%Y %H:%M:%S'),

        ('datetime', 0),  # field pos 0
        ('bid', 1),  # default field pos 1
        ('ask', 2),  # defult field pos 2
    )


class St(bt.Strategy):
    def next(self):
        dtstr = self.data.datetime.datetime().isoformat()
        print('%4d: %s - Bid %.4f - %.4f Ask' %
              (len(self), dtstr, self.data.bid[0], self.data.ask[0]))


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    data = BidAskCSV(dataname='../../datas/bidask.csv')
    cerebro.adddata(data)
    cerebro.addstrategy(St)

    cerebro.run()
