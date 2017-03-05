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

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)

    # Load the Data
    datapath = args.dataname or '../../datas/ticksample.csv'

    data = btfeeds.GenericCSVData(
        dataname=datapath,
        dtformat='%Y-%m-%dT%H:%M:%S.%f',
        timeframe=bt.TimeFrame.Ticks,
    )

    # Handy dictionary for the argument timeframe conversion
    tframes = dict(
        ticks=bt.TimeFrame.Ticks,
        microseconds=bt.TimeFrame.MicroSeconds,
        seconds=bt.TimeFrame.Seconds,
        minutes=bt.TimeFrame.Minutes,
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)

    # Resample the data
    cerebro.resampledata(
        data,
        timeframe=tframes[args.timeframe],
        compression=args.compression,
        bar2edge=not args.nobar2edge,
        adjbartime=not args.noadjbartime,
        rightedge=args.rightedge)

    if args.writer:
        # add a writer
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resampling script down to tick data')

    parser.add_argument('--dataname', default='', required=False,
                        help='File Data to Load')

    parser.add_argument('--timeframe', default='ticks', required=False,
                        choices=['ticks', 'microseconds', 'seconds',
                                 'minutes', 'daily', 'weekly', 'monthly'],
                        help='Timeframe to resample to')

    parser.add_argument('--compression', default=1, required=False, type=int,
                        help=('Compress n bars into 1'))

    parser.add_argument('--nobar2edge', required=False, action='store_true',
                        help=('Do not Resample IntraDay Timed Bars to edges'))

    parser.add_argument('--noadjbartime', required=False,
                        action='store_true',
                        help=('Do not adjust the time bar to meet the edges'))

    parser.add_argument('--rightedge', required=False, action='store_true',
                        help=('Resample to right edge of boundary'))

    parser.add_argument('--writer', required=False, action='store_true',
                        help=('Add a Writer'))

    parser.add_argument('--wrcsv', required=False, action='store_true',
                        help=('Add CSV to the Writer'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
