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
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt


def runstrat(pargs=None):
    args = parse_args(pargs)

    # Create a cerebro
    cerebro = bt.Cerebro()

    if args.cash is not None:
        cerebro.broker.set_cash(args.cash)

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    # Create the 1st data
    data = bt.feeds.BacktraderCSVData(
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    cerebro.adddata(data)  # Add the data to cerebro

    # Add the strategy
    cerebro.addstrategy(bt.strategies.SMA_CrossOver)

    tframes = dict(
        days=bt.TimeFrame.Days,
        weeks=bt.TimeFrame.Weeks,
        months=bt.TimeFrame.Months,
        years=bt.TimeFrame.Years)

    # Add the Analyzers
    cerebro.addanalyzer(bt.analyzers.TimeReturn,
                        timeframe=tframes[args.tframe])

    shkwargs = dict()
    if args.annualize:
        shkwargs['annualize'] = True

    if args.riskfreerate is not None:
        shkwargs['riskfreerate'] = args.riskfreerate

    if args.factor is not None:
        shkwargs['factor'] = args.factor

    if args.stddev_sample:
        shkwargs['stddev_sample'] = True

    if args.no_convertrate:
        shkwargs['convertrate'] = False

    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                        timeframe=tframes[args.tframe],
                        **shkwargs)

    # Add a writer to get output
    cerebro.addwriter(bt.WriterFile, csv=args.writercsv, rounding=4)

    cerebro.run()  # And run it

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
        description='TimeReturns and SharpeRatio')

    parser.add_argument('--data', '-d',
                        default='../../datas/2005-2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--cash', default=None, type=float, required=False,
                        help='Starting Cash')

    parser.add_argument('--fromdate', '-f',
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--writercsv', '-wcsv', action='store_true',
                        help='Tell the writer to produce a csv stream')

    parser.add_argument('--tframe', '--timeframe', default='years',
                        required=False,
                        choices=['days', 'weeks', 'months', 'years'],
                        help='TimeFrame for the Returns/Sharpe calculations')

    parser.add_argument('--annualize', required=False, action='store_true',
                        help='Annualize Sharpe Ratio')

    parser.add_argument('--riskfreerate', required=False, action='store',
                        type=float, default=None,
                        help='Riskfree Rate (annual) for Sharpe')

    parser.add_argument('--factor', required=False, action='store',
                        type=float, default=None,
                        help=('Riskfree Rate conversion factor for Sharpe '
                              'to downgrade riskfree rate to timeframe'))

    parser.add_argument('--stddev-sample', required=False, action='store_true',
                        help='Consider Bessels correction for stddeviation')

    parser.add_argument('--no-convertrate', required=False,
                        action='store_true',
                        help=('Upgrade returns to target timeframe rather than'
                              'downgrading the riskfreerate'))

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
