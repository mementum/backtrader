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


class NYSE_2016(bt.TradingCalendar):
    params = dict(
        holidays=[
            datetime.date(2016, 1, 1),
            datetime.date(2016, 1, 18),
            datetime.date(2016, 2, 15),
            datetime.date(2016, 3, 25),
            datetime.date(2016, 5, 30),
            datetime.date(2016, 7, 4),
            datetime.date(2016, 9, 5),
            datetime.date(2016, 11, 24),
            datetime.date(2016, 12, 26),
        ],
        earlydays=[
            (datetime.date(2016, 11, 25),
             datetime.time(9, 30), datetime.time(13, 1))
        ],
        open=datetime.time(9, 30),
        close=datetime.time(16, 0),
    )


class St(bt.Strategy):
    params = dict(
    )

    def __init__(self):
        pass

    def prenext(self):
        self.next()

    def next(self):
        print('Strategy len {} datetime {}'.format(
            len(self), self.datetime.datetime()), end=' ')

        print('Data0 len {} datetime {}'.format(
            len(self.data0), self.data0.datetime.datetime()), end=' ')

        if len(self.data1):
            print('Data1 len {} datetime {}'.format(
                len(self.data1), self.data1.datetime.datetime()))
        else:
            print()


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    # kwargs = dict(tz='US/Eastern')
    # import pytz
    # tz = tzinput = pytz.timezone('Europe/Berlin')
    tzinput = 'Europe/Berlin'
    # tz = tzinput
    tz = 'US/Eastern'
    kwargs = dict(tzinput=tzinput, tz=tz)

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    cerebro.adddata(data0)

    d1 = cerebro.resampledata(data0,
                              timeframe=getattr(bt.TimeFrame, args.timeframe))
    # d1.plotinfo.plotmaster = data0
    # d1.plotinfo.sameaxis = False

    if args.pandascal:
        cerebro.addcalendar(args.pandascal)
    elif args.owncal:
        cerebro.addcalendar(NYSE_2016())  # or NYSE_2016() to pass an instance

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Trading Calendar Sample'
        )
    )

    parser.add_argument('--data0', default='yhoo-2016-11.csv',
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='2016-01-01',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2016-12-31',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument('--pandascal', required=False, action='store',
                        default='', help='Name of trading calendar to use')

    pgroup.add_argument('--owncal', required=False, action='store_true',
                        help='Apply custom NYSE 2016 calendar')

    parser.add_argument('--timeframe', required=False, action='store',
                        default='Days', choices=['Days'],
                        help='Timeframe to resample to')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
