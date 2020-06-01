#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
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

import argparse
import datetime
import os.path
import time
import sys


import backtrader as bt
from backtrader.utils.py3 import bytes


DATAFORMATS = dict(
    btcsv=bt.feeds.BacktraderCSVData,
    vchartcsv=bt.feeds.VChartCSVData,
    vchart=bt.feeds.VChartData,
    vcdata=bt.feeds.VCData,
    vcfile=bt.feeds.VChartFile,
    ibdata=bt.feeds.IBData,
    sierracsv=bt.feeds.SierraChartCSVData,
    mt4csv=bt.feeds.MT4CSVData,
    yahoocsv=bt.feeds.YahooFinanceCSVData,
    yahoocsv_unreversed=bt.feeds.YahooFinanceCSVData,
    yahoo=bt.feeds.YahooFinanceData,
)


class RewriteStrategy(bt.Strategy):
    params = (
        ('separator', ','),
        ('outfile', None),
    )

    def start(self):
        if self.p.outfile is None:
            self.f = sys.stdout
        else:
            self.f = open(self.p.outfile, 'wb')

        if self.data._timeframe < bt.TimeFrame.Days:
            headers = 'Date,Time,Open,High,Low,Close,Volume,OpenInterest'
        else:
            headers = 'Date,Open,High,Low,Close,Volume,OpenInterest'

        headers += '\n'
        self.f.write(bytes(headers))

    def next(self):
        fields = list()
        dt = self.data.datetime.date(0).strftime('%Y-%m-%d')
        fields.append(dt)
        if self.data._timeframe < bt.TimeFrame.Days:
            tm = self.data.datetime.time(0).strftime('%H:%M:%S')
            fields.append(tm)

        o = '%.2f' % self.data.open[0]
        fields.append(o)
        h = '%.2f' % self.data.high[0]
        fields.append(h)
        l = '%.2f' % self.data.low[0]
        fields.append(l)
        c = '%.2f' % self.data.close[0]
        fields.append(c)
        v = '%d' % self.data.volume[0]
        fields.append(v)
        oi = '%d' % self.data.openinterest[0]
        fields.append(oi)

        txt = self.p.separator.join(fields)
        txt += '\n'
        self.f.write(bytes(txt))


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()

    dfkwargs = dict()
    if args.format == 'yahoo_unreversed':
        dfkwargs['reverse'] = True

    fmtstr = '%Y-%m-%d'
    if args.fromdate:
        dtsplit = args.fromdate.split('T')
        if len(dtsplit) > 1:
            fmtstr += 'T%H:%M:%S'

        fromdate = datetime.datetime.strptime(args.fromdate, fmtstr)
        dfkwargs['fromdate'] = fromdate

    fmtstr = '%Y-%m-%d'
    if args.todate:
        dtsplit = args.todate.split('T')
        if len(dtsplit) > 1:
            fmtstr += 'T%H:%M:%S'
        todate = datetime.datetime.strptime(args.todate, fmtstr)
        dfkwargs['todate'] = todate

    dfcls = DATAFORMATS[args.format]
    data = dfcls(dataname=args.infile, **dfkwargs)
    cerebro.adddata(data)

    cerebro.addstrategy(RewriteStrategy,
                        separator=args.separator,
                        outfile=args.outfile)

    cerebro.run(stdstats=False)

    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Rewrite formats to BacktraderCSVData format')

    parser.add_argument('--format', '-fmt', required=False,
                        choices=DATAFORMATS.keys(),
                        default=next(iter(DATAFORMATS)),
                        help='File to be read in')

    parser.add_argument('--infile', '-i', required=True,
                        help='File to be read in')

    parser.add_argument('--outfile', '-o', default=None, required=False,
                        help='File to write to')

    parser.add_argument('--fromdate', '-f', required=False,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t', required=False,
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--separator', '-s', required=False, default=',',
                        help='Plot the read data')

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
