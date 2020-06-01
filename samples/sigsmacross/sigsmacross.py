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

import backtrader as bt


class SmaCross(bt.SignalStrategy):
    params = dict(sma1=10, sma2=20)

    def notify_order(self, order):
        if not order.alive():
            print('{} {} {}@{}'.format(
                bt.num2date(order.executed.dt),
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price)
            )

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.params.sma1)
        sma2 = bt.ind.SMA(period=self.params.sma2)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    data0 = bt.feeds.YahooFinanceData(
        dataname=args.data,
        fromdate=datetime.datetime.strptime(args.fromdate, '%Y-%m-%d'),
        todate=datetime.datetime.strptime(args.todate, '%Y-%m-%d'))
    cerebro.adddata(data0)

    cerebro.addstrategy(SmaCross, **(eval('dict(' + args.strat + ')')))
    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)

    cerebro.run()
    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='sigsmacross')

    parser.add_argument('--data', required=False, default='YHOO',
                        help='Yahoo Ticker')

    parser.add_argument('--fromdate', required=False, default='2011-01-01',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False, default='2012-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=10000, help=('Starting cash'))

    parser.add_argument('--stake', required=False, action='store', type=int,
                        default=1, help=('Stake to apply'))

    parser.add_argument('--strat', required=False, action='store', default='',
                        help=('Arguments for the strategy'))

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
