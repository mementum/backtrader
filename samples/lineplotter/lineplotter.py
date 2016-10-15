#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
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
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt


class St(bt.Strategy):
    params = (
        ('ondata', False),
    )

    def __init__(self):
        if not self.p.ondata:
            a = self.data.high - self.data.low
        else:
            a = 1.05 * (self.data.high + self.data.low) / 2.0

        b = bt.LinePlotterIndicator(a, name='hilo')
        b.plotinfo.subplot = not self.p.ondata


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()

    dkwargs = dict()
    # Get the dates from the args
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
        dkwargs['fromdate'] = fromdate
    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
        dkwargs['todate'] = todate

    data = bt.feeds.BacktraderCSVData(dataname=args.data, **dkwargs)
    cerebro.adddata(data)

    cerebro.addstrategy(St, ondata=args.ondata)
    cerebro.run(stdstats=False)

    # Plot if requested
    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Fake Indicator')

    parser.add_argument('--data', '-d',
                        default='../../datas/2005-2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f',
                        default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--ondata', '-o', action='store_true',
                        help='Plot fake indicator on the data')

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
