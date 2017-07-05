#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2017 Daniel Rodriguez
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


ORDER_HISTORY = (
    ('2005-02-01', 1, 2984.63),
    ('2005-03-04', -1, 3079.93),
    ('2005-03-08', 1, 3113.82),
    ('2005-03-22', -1, 3040.55),
    ('2005-04-08', 1, 3092.07),
    ('2005-04-20', -1, 2957.92),
    ('2005-05-13', 1, 2991.71),
    ('2005-08-19', -1, 3284.35),
    ('2005-08-22', 1, 3328.84),
    ('2005-08-25', -1, 3293.69),
    ('2005-09-12', 1, 3361.1),
    ('2005-10-18', -1, 3356.73),
    ('2005-11-09', 1, 3361.92),
    ('2006-01-24', -1, 3544.78),
    ('2006-02-06', 1, 3678.87),
    ('2006-03-13', -1, 3801.03),
    ('2006-03-20', 1, 3833.25),
    ('2006-04-13', -1, 3777.24),
    ('2006-05-02', 1, 3839.24),
    ('2006-05-16', -1, 3711.46),
    ('2006-06-30', 1, 3592.01),
    ('2006-07-21', -1, 3580.53),
    ('2006-08-01', 1, 3687.82),
    ('2006-09-14', -1, 3809.08),
    ('2006-09-25', 1, 3815.13),
    ('2006-12-01', -1, 3993.03),
    ('2006-12-18', 1, 4140.99),
)


class SmaCross(bt.SignalStrategy):
    params = dict(sma1=10, sma2=20)

    def notify_order(self, order):
        if not order.alive():
            print(','.join(str(x) for x in
                           (self.data.num2date(order.executed.dt).date(),
                            order.executed.size * 1 if order.isbuy() else -1,
                            order.executed.price)))

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))

    def __init__(self):
        print('Creating Signal Strategy')
        sma1 = bt.ind.SMA(period=self.params.sma1)
        sma2 = bt.ind.SMA(period=self.params.sma2)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


class St(bt.Strategy):
    params = dict(
    )

    def notify_order(self, order):
        if not order.alive():
            print(','.join(str(x) for x in
                           (self.data.num2date(order.executed.dt).date(),
                            order.executed.size * 1 if order.isbuy() else -1,
                            order.executed.price)))

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))

    def __init__(self):
        print('Creating Empty Strategy')
        pass

    def next(self):
        pass


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    cerebro.adddata(data0)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))

    # Strategy
    if not args.order_history:
        cerebro.addstrategy(SmaCross, **eval('dict(' + args.strat + ')'))
    else:
        cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))
        cerebro.add_order_history(ORDER_HISTORY, notify=True)

    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Order History Sample'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt',
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--order-history', required=False, action='store_true',
                        help='use order history')

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

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
