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
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
import backtrader.filters as btfilters


def runstrat():
    args = parse_args()

    # 创建 cerebro 实体
    cerebro = bt.Cerebro(stdstats=False)

    # 添加 strategy
    cerebro.addstrategy(bt.Strategy)

    # 从参数中读取日期
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    data = btfeeds.BacktraderCSVData(
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    if args.calendar:
        if args.fprice is not None:
            args.fprice = float(args.fprice)

        data.addfilter(
            btfilters.CalendarDays,
            fill_price=args.fprice,
            fill_vol=args.fvol)

    # 添加处理后的 data，而不是原始 data
    cerebro.adddata(data)

    # 如果需要，添加 Simple Moving Average
    if args.sma:
        cerebro.addindicator(btind.SMA, period=args.period)

    # 添加带 CSV 选项的 writer
    if args.writer:
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)

    # 运行整个系统
    cerebro.run()

    # 如果需要则绘图
    if args.plot:
        cerebro.plot(style='bar', numfigs=args.numfigs, volume=False)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Calendar Days Filter Sample')

    parser.add_argument('--data', '-d',
                        default='../../datas/2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f',
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--calendar', '-cal', required=False,
                        action='store_true',
                        help='Add a CalendarDays filter')

    parser.add_argument('--fprice', required=False, default=None,
                        help='Use as fill for price (None for previous close)')

    parser.add_argument('--fvol', required=False, default=0.0,
                        type=float,
                        help='Use as fill volume for missing bar (def: 0.0)')

    parser.add_argument('--sma', required=False,
                        action='store_true',
                        help='Add a Simple Moving Average')

    parser.add_argument('--period', default=15, type=int,
                        help='Period to apply to the Simple Moving Average')

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
    runstrat()
