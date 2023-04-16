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
from __future__ import (absolute_import, division, print_function,)
#                        unicode_literals)

import argparse
import datetime

import backtrader as bt
import backtrader.feeds as btfeeds


class St(bt.Strategy):
    def next(self):
        print(','.join(str(x) for x in [
            self.data.datetime.datetime(),
            self.data.open[0], self.data.high[0],
            self.data.high[0], self.data.close[0],
            self.data.volume[0]]))


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()

    data = btfeeds.GenericCSVData(
        dataname=args.data,
        dtformat='%d/%m/%y',
        # tmformat='%H%M%S',  # already the default value
        # datetime=0,  # position at default
        time=1,  # position of time
        open=5,  # position of open
        high=5,
        low=5,
        close=5,
        volume=7,
        openinterest=-1,  # -1 for not present
        timeframe=bt.TimeFrame.Ticks)

    cerebro.resampledata(data,
                         timeframe=bt.TimeFrame.Ticks,
                         compression=args.compression)

    cerebro.addstrategy(St)

    cerebro.run()
    if args.plot:
        cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='BidAsk to OHLC')

    parser.add_argument('--data', required=False,
                        default='../../datas/bidask2.csv',
                        help='Data file to be read in')

    parser.add_argument('--compression', required=False, default=2, type=int,
                        help='How much to compress the bars')

    parser.add_argument('--plot', required=False, action='store_true',
                        help='Plot the vars')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
