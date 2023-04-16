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
import math

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.utils.flushfile
import backtrader.filters as btfilters

from relativevolume import RelativeVolume


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    # Get the session times to pass them to the indicator
    # datetime.time has no strptime ...
    dtstart = datetime.datetime.strptime(args.tstart, '%H:%M')
    dtend = datetime.datetime.strptime(args.tend, '%H:%M')

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(
        dataname=args.data,
        fromdate=fromdate,
        todate=todate,
        timeframe=bt.TimeFrame.Minutes,
        compression=1,
        sessionstart=dtstart,  # internally just the "time" part will be used
        sessionend=dtend,  # internally just the "time" part will be used
    )

    if args.filter:
        data.addfilter(btfilters.SessionFilter)

    if args.filler:
        data.addfilter(btfilters.SessionFiller, fill_vol=args.fvol)

    # Add the data to cerebro
    cerebro.adddata(data)

    if args.relvol:
        # Calculate backward period - tend tstart are in same day
        # + 1 to include last moment of the interval dstart <-> dtend
        td = ((dtend - dtstart).seconds // 60) + 1
        cerebro.addindicator(RelativeVolume,
                             period=td,
                             volisnan=math.isnan(args.fvol))

    # Add an empty strategy
    cerebro.addstrategy(bt.Strategy)

    # Add a writer with CSV
    if args.writer:
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)

    # And run it - no trading - disable stdstats
    cerebro.run(stdstats=False)

    # Plot if requested
    if args.plot:
        cerebro.plot(numfigs=args.numfigs, volume=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description='DataFilter/DataFiller Sample')

    parser.add_argument('--data', '-d',
                        default='../../datas/2006-01-02-volume-min-001.txt',
                        help='data to add to the system')

    parser.add_argument('--filter', '-ft', action='store_true',
                        help='Filter using session start/end times')

    parser.add_argument('--filler', '-fl', action='store_true',
                        help='Fill missing bars inside start/end times')

    parser.add_argument('--fvol', required=False, default=0.0,
                        type=float,
                        help='Use as fill volume for missing bar (def: 0.0)')

    parser.add_argument('--tstart', '-ts',
                        # default='09:14:59',
                        # help='Start time for the Session Filter (%H:%M:%S)')
                        default='09:15',
                        help='Start time for the Session Filter (HH:MM)')

    parser.add_argument('--tend', '-te',
                        # default='17:15:59',
                        # help='End time for the Session Filter (%H:%M:%S)')
                        default='17:15',
                        help='End time for the Session Filter (HH:MM)')

    parser.add_argument('--relvol', '-rv', action='store_true',
                        help='Add relative volume indicator')

    parser.add_argument('--fromdate', '-f',
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--writer', '-w', action='store_true',
                        help='Add a writer to cerebro')

    parser.add_argument('--wrcsv', '-wc', action='store_true',
                        help='Enable CSV Output in the writer')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
