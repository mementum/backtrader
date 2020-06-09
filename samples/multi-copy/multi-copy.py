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
import random

import backtrader as bt


class TheStrategy(bt.Strategy):
    '''
    This strategy is capable of:

      - Going Long with a Moving Average upwards CrossOver

      - Going Long again with a MACD upwards CrossOver

      - Closing the aforementioned longs with the corresponding downwards
        crossovers
    '''

    params = (
        ('myname', None),
        ('dtarget', None),
        ('stake', 100),
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('sma1', 10),
        ('sma2', 30),
    )

    def notify_order(self, order):
        if not order.alive():
            if not order.isbuy():  # going flat
                self.order = 0

            if order.status == order.Completed:
                tfields = [self.p.myname,
                           len(self),
                           order.data.datetime.date(),
                           order.data._name,
                           'BUY' * order.isbuy() or 'SELL',
                           order.executed.size, order.executed.price]

                print(','.join(str(x) for x in tfields))

    def __init__(self):
        # Choose data to buy from
        self.dtarget = self.getdatabyname(self.p.dtarget)

        # Create indicators
        sma1 = bt.ind.SMA(self.dtarget, period=self.p.sma1)
        sma2 = bt.ind.SMA(self.dtarget, period=self.p.sma2)
        self.smasig = bt.ind.CrossOver(sma1, sma2)

        macd = bt.ind.MACD(self.dtarget,
                           period_me1=self.p.macd1,
                           period_me2=self.p.macd2,
                           period_signal=self.p.macdsig)

        # Cross of macd.macd and macd.signal
        self.macdsig = bt.ind.CrossOver(macd.macd, macd.signal)

    def start(self):
        self.order = 0  # sentinel to avoid operrations on pending order

        tfields = ['Name', 'Length', 'Datetime', 'Operation/Names',
                   'Position1.Size', 'Position2.Size']
        print(','.join(str(x) for x in tfields))

    def next(self):
        tfields = [self.p.myname,
                   len(self),
                   self.data.datetime.date(),
                   self.getposition(self.data0).size]
        if len(self.datas) > 1:
            tfields.append(self.getposition(self.data1).size)

        print(','.join(str(x) for x in tfields))

        buysize = self.p.stake // 2  # let each signal buy half
        if self.macdsig[0] > 0.0:
            self.buy(data=self.dtarget, size=buysize)

        if self.smasig[0] > 0.0:
            self.buy(data=self.dtarget, size=buysize)

        size = self.getposition(self.dtarget).size

        # if 2x in the market, let each potential close ... close 1/2
        if size == self.p.stake:
            size //= 2

        if self.macdsig[0] < 0.0:
            self.close(data=self.dtarget, size=size)

        if self.smasig[0] < 0.0:
            self.close(data=self.dtarget, size=size)


class TheStrategy2(TheStrategy):
    '''
    Subclass of TheStrategy to simply change the parameters

    '''
    params = (
        ('stake', 200),
        ('macd1', 15),
        ('macd2', 22),
        ('macdsig', 7),
        ('sma1', 15),
        ('sma2', 50),
    )


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    dkwargs = dict()
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
        dkwargs['fromdate'] = fromdate

    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
        dkwargs['todate'] = todate

    # if dataset is None, args.data has been given
    data0 = bt.feeds.YahooFinanceCSVData(dataname=args.data0, **dkwargs)
    cerebro.adddata(data0, name='MyData0')

    st0kwargs = dict()
    if args.st0 is not None:
        tmpdict = eval('dict(' + args.st0 + ')')  # args were passed
        st0kwargs.update(tmpdict)

    cerebro.addstrategy(TheStrategy,
                        myname='St1', dtarget='MyData0', **st0kwargs)

    if args.copydata:
        data1 = data0.copyas('MyData1')
        cerebro.adddata(data1)
        dtarget = 'MyData1'

    else:  # use same target
        dtarget = 'MyData0'

    st1kwargs = dict()
    if args.st1 is not None:
        tmpdict = eval('dict(' + args.st1 + ')')  # args were passed
        st1kwargs.update(tmpdict)

    cerebro.addstrategy(TheStrategy2,
                        myname='St2', dtarget=dtarget, **st1kwargs)

    results = cerebro.run()

    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Tharp example with MACD')

    # pgroup = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--data0', required=False,
                        default='../../datas/yhoo-1996-2014.txt',
                        help='Specific data0 to be read in')

    parser.add_argument('--fromdate', required=False,
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,
                        default='2006-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store',
                        type=float, default=50000,
                        help=('Cash to start with'))

    parser.add_argument('--copydata', required=False, action='store_true',
                        help=('Copy Data for 2nd strategy'))

    parser.add_argument('--st0', required=False, action='store',
                        default=None,
                        help=('Params for 1st strategy: as a list of comma '
                              'separated name=value pairs like: '
                              'stake=100,macd1=12,macd2=26,macdsig=9,'
                              'sma1=10,sma2=30'))

    parser.add_argument('--st1', required=False, action='store',
                        default=None,
                        help=('Params for 1st strategy: as a list of comma '
                              'separated name=value pairs like: '
                              'stake=200,macd1=15,macd2=22,macdsig=7,'
                              'sma1=15,sma2=50'))

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
