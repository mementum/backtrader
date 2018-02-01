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


class BaseStrategy(bt.Strategy):
    params = dict(
        fast_ma=10,
        slow_ma=20,
    )

    def __init__(self):
        # omitting a data implies self.datas[0] (aka self.data and self.data0)
        fast_ma = bt.ind.EMA(period=self.p.fast_ma)
        slow_ma = bt.ind.EMA(period=self.p.slow_ma)
        # our entry point
        self.crossup = bt.ind.CrossUp(fast_ma, slow_ma)


class ManualStopOrStopTrail(BaseStrategy):
    params = dict(
        stop_loss=0.02,  # price is 2% less than the entry point
        trail=False,
    )

    def notify_order(self, order):
        if not order.status == order.Completed:
            return  # discard any other notification

        if not self.position:  # we left the market
            print('SELL@price: {:.2f}'.format(order.executed.price))
            return

        # We have entered the market
        print('BUY @price: {:.2f}'.format(order.executed.price))

        if not self.p.trail:
            stop_price = order.executed.price * (1.0 - self.p.stop_loss)
            self.sell(exectype=bt.Order.Stop, price=stop_price)
        else:
            self.sell(exectype=bt.Order.StopTrail, trailamount=self.p.trail)

    def next(self):
        if not self.position and self.crossup > 0:
            # not in the market and signal triggered
            self.buy()


class ManualStopOrStopTrailCheat(BaseStrategy):
    params = dict(
        stop_loss=0.02,  # price is 2% less than the entry point
        trail=False,
    )

    def __init__(self):
        super().__init__()
        self.broker.set_coc(True)

    def notify_order(self, order):
        if not order.status == order.Completed:
            return  # discard any other notification

        if not self.position:  # we left the market
            print('SELL@price: {:.2f}'.format(order.executed.price))
            return

        # We have entered the market
        print('BUY @price: {:.2f}'.format(order.executed.price))

    def next(self):
        if not self.position and self.crossup > 0:
            # not in the market and signal triggered
            self.buy()

            if not self.p.trail:
                stop_price = self.data.close[0] * (1.0 - self.p.stop_loss)
                self.sell(exectype=bt.Order.Stop, price=stop_price)
            else:
                self.sell(exectype=bt.Order.StopTrail,
                          trailamount=self.p.trail)


class AutoStopOrStopTrail(BaseStrategy):
    params = dict(
        stop_loss=0.02,  # price is 2% less than the entry point
        trail=False,
        buy_limit=False,
    )

    buy_order = None  # default value for a potential buy_order

    def notify_order(self, order):
        if order.status == order.Cancelled:
            print('CANCEL@price: {:.2f} {}'.format(
                order.executed.price, 'buy' if order.isbuy() else 'sell'))
            return

        if not order.status == order.Completed:
            return  # discard any other notification

        if not self.position:  # we left the market
            print('SELL@price: {:.2f}'.format(order.executed.price))
            return

        # We have entered the market
        print('BUY @price: {:.2f}'.format(order.executed.price))

    def next(self):
        if not self.position and self.crossup > 0:
            if self.buy_order:  # something was pending
                self.cancel(self.buy_order)

            # not in the market and signal triggered
            if not self.p.buy_limit:
                self.buy_order = self.buy(transmit=False)
            else:
                price = self.data.close[0] * (1.0 - self.p.buy_limit)

                # transmit = False ... await child order before transmission
                self.buy_order = self.buy(price=price, exectype=bt.Order.Limit,
                                          transmit=False)

            # Setting parent=buy_order ... sends both together
            if not self.p.trail:
                stop_price = self.data.close[0] * (1.0 - self.p.stop_loss)
                self.sell(exectype=bt.Order.Stop, price=stop_price,
                          parent=self.buy_order)
            else:
                self.sell(exectype=bt.Order.StopTrail,
                          trailamount=self.p.trail,
                          parent=self.buy_order)


APPROACHES = dict(
    manual=ManualStopOrStopTrail,
    manualcheat=ManualStopOrStopTrailCheat,
    auto=AutoStopOrStopTrail,
)


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
    StClass = APPROACHES[args.approach]
    cerebro.addstrategy(StClass, **eval('dict(' + args.strat + ')'))

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Stop-Loss Approaches'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt',
                        required=False, help='Data to read in')

    # Strategy to choose
    parser.add_argument('approach', choices=APPROACHES.keys(),
                        help='Stop approach to use')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
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

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
