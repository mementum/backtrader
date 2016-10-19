#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2016 Daniel Rodriguez
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


class TheStrategy(bt.SignalStrategy):
    params = dict(rsi_per=14, rsi_upper=65.0, rsi_lower=35.0, rsi_out=50.0,
                  warmup=35)

    def notify_order(self, order):
        super(TheStrategy, self).notify_order(order)
        if order.status == order.Completed:
            print('%s: Size: %d @ Price %f' %
                  ('buy' if order.isbuy() else 'sell',
                   order.executed.size, order.executed.price))

            d = order.data
            print('Close[-1]: %f - Open[0]: %f' % (d.close[-1], d.open[0]))

    def __init__(self):
        # Original code needs artificial warmup phase - hidden sma to replic
        if self.p.warmup:
            bt.indicators.SMA(period=self.p.warmup, plot=False)

        rsi = bt.indicators.RSI(period=self.p.rsi_per,
                                upperband=self.p.rsi_upper,
                                lowerband=self.p.rsi_lower)

        crossup = bt.ind.CrossUp(rsi, self.p.rsi_lower)
        self.signal_add(bt.SIGNAL_LONG, crossup)
        self.signal_add(bt.SIGNAL_LONGEXIT, -(rsi > self.p.rsi_out))

        crossdown = bt.ind.CrossDown(rsi, self.p.rsi_upper)
        self.signal_add(bt.SIGNAL_SHORT, -crossdown)
        self.signal_add(bt.SIGNAL_SHORTEXIT, rsi < self.p.rsi_out)


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.set_coc(args.coc)
    data0 = bt.feeds.YahooFinanceData(
        dataname=args.data,
        fromdate=datetime.datetime.strptime(args.fromdate, '%Y-%m-%d'),
        todate=datetime.datetime.strptime(args.todate, '%Y-%m-%d'),
        round=False)

    cerebro.adddata(data0)

    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)
    cerebro.addstrategy(TheStrategy, **(eval('dict(' + args.strat + ')')))
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell, barplot=True)

    cerebro.run(stdstats=False)
    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample after post at keithselover.wordpress.com')

    parser.add_argument('--data', required=False, default='XOM',
                        help='Yahoo Ticker')

    parser.add_argument('--fromdate', required=False, default='2012-09-01',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False, default='2016-01-01',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=100000, help=('Cash to start with'))

    parser.add_argument('--stake', required=False, action='store', type=int,
                        default=100, help=('Cash to start with'))

    parser.add_argument('--coc', required=False, action='store_true',
                        help=('Buy on close of same bar as order is issued'))

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
