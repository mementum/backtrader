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
import datetime
import time

from backtrader.utils.py3 import range

import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds


class OptimizeStrategy(bt.Strategy):
    params = (('smaperiod', 15),
              ('macdperiod1', 12),
              ('macdperiod2', 26),
              ('macdperiod3', 9),
              )

    def __init__(self):
        # Add indicators to add load

        btind.SMA(period=self.p.smaperiod)
        btind.MACD(period_me1=self.p.macdperiod1,
                   period_me2=self.p.macdperiod2,
                   period_signal=self.p.macdperiod3)


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(maxcpus=args.maxcpus,
                         runonce=not args.no_runonce,
                         exactbars=args.exactbars,
                         optdatas=not args.no_optdatas,
                         optreturn=not args.no_optreturn)

    # Add a strategy
    cerebro.optstrategy(
        OptimizeStrategy,
        smaperiod=range(args.ma_low, args.ma_high),
        macdperiod1=range(args.m1_low, args.m1_high),
        macdperiod2=range(args.m2_low, args.m2_high),
        macdperiod3=range(args.m3_low, args.m3_high),
    )

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # clock the start of the process
    tstart = time.clock()

    # Run over everything
    stratruns = cerebro.run()

    # clock the end of the process
    tend = time.clock()

    print('==================================================')
    for stratrun in stratruns:
        print('**************************************************')
        for strat in stratrun:
            print('--------------------------------------------------')
            print(strat.p._getkwargs())
    print('==================================================')

    # print out the result
    print('Time used:', str(tend - tstart))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Optimization',
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        '--data', '-d',
        default='../../datas/2006-day-001.txt',
        help='data to add to the system')

    parser.add_argument(
        '--fromdate', '-f',
        default='2006-01-01',
        help='Starting date in YYYY-MM-DD format')

    parser.add_argument(
        '--todate', '-t',
        default='2006-12-31',
        help='Starting date in YYYY-MM-DD format')

    parser.add_argument(
        '--maxcpus', '-m',
        type=int, required=False, default=0,
        help=('Number of CPUs to use in the optimization'
              '\n'
              '  - 0 (default): use all available CPUs\n'
              '  - 1 -> n: use as many as specified\n'))

    parser.add_argument(
        '--no-runonce', action='store_true', required=False,
        help='Run in next mode')

    parser.add_argument(
        '--exactbars', required=False, type=int, default=0,
        help=('Use the specified exactbars still compatible with preload\n'
              '  0 No memory savings\n'
              '  -1 Moderate memory savings\n'
              '  -2 Less moderate memory savings\n'))

    parser.add_argument(
        '--no-optdatas', action='store_true', required=False,
        help='Do not optimize data preloading in optimization')

    parser.add_argument(
        '--no-optreturn', action='store_true', required=False,
        help='Do not optimize the returned values to save time')

    parser.add_argument(
        '--ma_low', type=int,
        default=10, required=False,
        help='SMA range low to optimize')

    parser.add_argument(
        '--ma_high', type=int,
        default=30, required=False,
        help='SMA range high to optimize')

    parser.add_argument(
        '--m1_low', type=int,
        default=12, required=False,
        help='MACD Fast MA range low to optimize')

    parser.add_argument(
        '--m1_high', type=int,
        default=20, required=False,
        help='MACD Fast MA range high to optimize')

    parser.add_argument(
        '--m2_low', type=int,
        default=26, required=False,
        help='MACD Slow MA range low to optimize')

    parser.add_argument(
        '--m2_high', type=int,
        default=30, required=False,
        help='MACD Slow MA range high to optimize')

    parser.add_argument(
        '--m3_low', type=int,
        default=9, required=False,
        help='MACD Signal range low to optimize')

    parser.add_argument(
        '--m3_high', type=int,
        default=15, required=False,
        help='MACD Signal range high to optimize')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
