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
from __future__ import (absolute_import, division, print_function,)
#                        unicode_literals)

import argparse
import datetime

import backtrader as bt
import backtrader.feeds as btfeeds


class St(bt.Strategy):
    def __init__(self):
        self.curdate = datetime.date.min
        self.elapsed = 0
        self.order = None

    def notify_order(self, order):
        curdtstr = self.data.datetime.datetime().strftime('%a %Y-%m-%d %H:%M:%S')
        if order.status in [order.Completed]:
            dtstr = bt.num2date(order.executed.dt).strftime('%a %Y-%m-%d %H:%M:%S')
            if order.isbuy():
                print('%s: BUY  EXECUTED, on:' % curdtstr, dtstr)
                self.order = None
            else:  # Sell
                print('%s: SELL EXECUTED, on:' % curdtstr, dtstr)

    def next(self):
        curdate = self.data.datetime.date()
        if curdate > self.curdate:
            self.elapsed += 1
            self.curdate = curdate

        dtstr = self.data.datetime.datetime().strftime('%a %Y-%m-%d %H:%M:%S')
        if self.position and self.elapsed == 2:
            print('%s: SELL CREATED' % dtstr)
            self.close(exectype=bt.Order.Close)
            self.elapsed = 0
        elif self.order is None and self.elapsed == 2:  # no pending order
            print('%s: BUY  CREATED' % dtstr)
            self.order = self.buy(exectype=bt.Order.Close)
            self.elapsed = 0


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()
    cerebro.adddata(getdata(args))
    cerebro.addstrategy(St)
    if args.eosbar:
        cerebro.broker.seteosbar(True)

    cerebro.run()


def getdata(args):

    dataformat = dict(
        bt=btfeeds.BacktraderCSVData,
        visualchart=btfeeds.VChartCSVData,
        sierrachart=btfeeds.SierraChartCSVData,
        yahoo=btfeeds.YahooFinanceCSVData,
        yahoo_unreversed=btfeeds.YahooFinanceCSVData
    )

    dfkwargs = dict()
    if args.csvformat == 'yahoo_unreversed':
        dfkwargs['reverse'] = True

    if args.fromdate:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
        dfkwargs['fromdate'] = fromdate

    if args.todate:
        fromdate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
        dfkwargs['todate'] = todate

    if args.tend is not None:
        # internally only the "time" part is used
        dfkwargs['sessionend'] = datetime.datetime.strptime(args.tend, '%H:%M')

    dfkwargs['dataname'] = args.infile
    dfcls = dataformat[args.csvformat]

    data = dfcls(**dfkwargs)

    return data


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Close Orders with daily data')

    parser.add_argument('--infile', '-i', required=False,
                        default='../../datas/2006-min-005.txt',
                        help='File to be read in')

    parser.add_argument('--csvformat', '-c', required=False, default='bt',
                        choices=['bt', 'visualchart', 'sierrachart',
                                 'yahoo', 'yahoo_unreversed'],
                        help='CSV Format')

    parser.add_argument('--fromdate', '-f', required=False, default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t', required=False, default=None,
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--eosbar', required=False, action='store_true',
                        help=('Consider a bar with the end of session time to'
                              'be the end of the session'))

    parser.add_argument('--tend', '-te',
                        default=None, required=False,
                        help='End time for the Session Filter (HH:MM)')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
