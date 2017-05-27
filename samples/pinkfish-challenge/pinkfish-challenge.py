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

import backtrader as bt
import backtrader.indicators as btind


class DayStepsCloseFilter(bt.with_metaclass(bt.MetaParams, object)):
    '''
    Replays a bar in 2 steps:

      - In the 1st step the "Open-High-Low" could be evaluated to decide if to
        act on the close (the close is still there ... should not be evaluated)

      - If a "Close" order has been executed

        In this 1st fragment the "Close" is replaced through the "open" althoug
        other alternatives would be possible like high - low average, or an
        algorithm based on where the "close" ac

      and

      - Open-High-Low-Close
    '''
    params = (
        ('cvol', 0.5),  # 0 -> 1 amount of volume to keep for close
    )

    def __init__(self, data):
        self.pendingbar = None

    def __call__(self, data):
        # Make a copy of the new bar and remove it from stream
        closebar = [data.lines[i][0] for i in range(data.size())]
        datadt = data.datetime.date()  # keep the date

        ohlbar = closebar[:]  # Make an open-high-low bar

        # Adjust volume
        ohlbar[data.Volume] = int(closebar[data.Volume] * (1.0 - self.p.cvol))

        dt = datetime.datetime.combine(datadt, data.p.sessionstart)
        ohlbar[data.DateTime] = data.date2num(dt)

        dt = datetime.datetime.combine(datadt, data.p.sessionend)
        closebar[data.DateTime] = data.date2num(dt)

        # Update stream
        data.backwards()  # remove the copied bar from stream
        # Overwrite the new data bar with our pending data - except start point
        if self.pendingbar is not None:
            data._updatebar(self.pendingbar)

        self.pendingbar = closebar  # update the pending bar to the new bar
        data._add2stack(ohlbar)  # Add the openbar to the stack for processing

        return False  # the length of the stream was not changed

    def last(self, data):
        '''Called when the data is no longer producing bars
        Can be called multiple times. It has the chance to (for example)
        produce extra bars'''
        if self.pendingbar is not None:
            data.backwards()  # remove delivered open bar
            data._add2stack(self.pendingbar)  # add remaining
            self.pendingbar = None  # No further action
            return True  # something delivered

        return False  # nothing delivered here


class DayStepsReplayFilter(bt.with_metaclass(bt.MetaParams, object)):
    '''
    Replays a bar in 2 steps:

      - In the 1st step the "Open-High-Low" could be evaluated to decide if to
        act on the close (the close is still there ... should not be evaluated)

      - If a "Close" order has been executed

        In this 1st fragment the "Close" is replaced through the "open" althoug
        other alternatives would be possible like high - low average, or an
        algorithm based on where the "close" ac

      and

      - Open-High-Low-Close
    '''
    params = (
        ('closevol', 0.5),  # 0 -> 1 amount of volume to keep for close
    )

    # replaying = True

    def __init__(self, data):
        self.lastdt = None
        pass

    def __call__(self, data):
        # Make a copy of the new bar and remove it from stream
        datadt = data.datetime.date()  # keep the date

        if self.lastdt == datadt:
            return False  # skip bars that come again in the filter

        self.lastdt = datadt  # keep ref to last seen bar

        # Make a copy of current data for ohlbar
        ohlbar = [data.lines[i][0] for i in range(data.size())]
        closebar = ohlbar[:]  # Make a copy for the close

        # replace close price with o-h-l average
        ohlprice = ohlbar[data.Open] + ohlbar[data.High] + ohlbar[data.Low]
        ohlbar[data.Close] = ohlprice / 3.0

        vol = ohlbar[data.Volume]  # adjust volume
        ohlbar[data.Volume] = vohl = int(vol * (1.0 - self.p.closevol))

        oi = ohlbar[data.OpenInterest]  # adjust open interst
        ohlbar[data.OpenInterest] = 0

        # Adjust times
        dt = datetime.datetime.combine(datadt, data.p.sessionstart)
        ohlbar[data.DateTime] = data.date2num(dt)

        # Ajust closebar to generate a single tick -> close price
        closebar[data.Open] = cprice = closebar[data.Close]
        closebar[data.High] = cprice
        closebar[data.Low] = cprice
        closebar[data.Volume] = vol - vohl
        ohlbar[data.OpenInterest] = oi

        # Adjust times
        dt = datetime.datetime.combine(datadt, data.p.sessionend)
        closebar[data.DateTime] = data.date2num(dt)

        # Update stream
        data.backwards(force=True)  # remove the copied bar from stream
        data._add2stack(ohlbar)  # add ohlbar to stack
        # Add 2nd part to stash to delay processing to next round
        data._add2stack(closebar, stash=True)

        return False  # the length of the stream was not changed


class St(bt.Strategy):
    params = (
        ('highperiod', 20),
        ('sellafter', 2),
        ('market', False),
    )

    def __init__(self):
        pass

    def start(self):
        self.callcounter = 0
        txtfields = list()
        txtfields.append('Calls')
        txtfields.append('Len Strat')
        txtfields.append('Len Data')
        txtfields.append('Datetime')
        txtfields.append('Open')
        txtfields.append('High')
        txtfields.append('Low')
        txtfields.append('Close')
        txtfields.append('Volume')
        txtfields.append('OpenInterest')
        print(','.join(txtfields))

        self.lcontrol = 0  # control if 1st or 2nd call
        self.inmarket = 0

        # Get the highest but delayed 1 ... to avoid "today"
        self.highest = btind.Highest(self.data.high,
                                     period=self.p.highperiod,
                                     subplot=False)

    def notify_order(self, order):
        if order.isbuy() and order.status == order.Completed:
            print('-- BUY Completed on:',
                  self.data.num2date(order.executed.dt).strftime('%Y-%m-%d'))
            print('-- BUY Price:', order.executed.price)

    def next(self):
        self.callcounter += 1

        txtfields = list()
        txtfields.append('%04d' % self.callcounter)
        txtfields.append('%04d' % len(self))
        txtfields.append('%04d' % len(self.data0))
        txtfields.append(self.data.datetime.datetime(0).isoformat())
        txtfields.append('%.2f' % self.data0.open[0])
        txtfields.append('%.2f' % self.data0.high[0])
        txtfields.append('%.2f' % self.data0.low[0])
        txtfields.append('%.2f' % self.data0.close[0])
        txtfields.append('%.2f' % self.data0.volume[0])
        txtfields.append('%.2f' % self.data0.openinterest[0])
        print(','.join(txtfields))

        if not self.position:
            if len(self.data) > self.lcontrol:
                if self.data.high == self.highest:  # today is highest!!!
                    print('High %.2f > Highest %.2f' %
                          (self.data.high[0], self.highest[0]))
                    print('LAST 19 highs:',
                          self.data.high.get(size=19, ago=-1))
                    print('-- BUY on date:',
                          self.data.datetime.date().strftime('%Y-%m-%d'))
                    ex = bt.Order.Market if self.p.market else bt.Order.Close
                    self.buy(exectype=ex)
                    self.inmarket = len(self)  # reset period in market

        else:  # in the market
            if (len(self) - self.inmarket) >= self.p.sellafter:
                self.sell()

        self.lcontrol = len(self.data)


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.set_eosbar(True)

    dkwargs = dict()
    if args.fromdate:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
        dkwargs['fromdate'] = fromdate

    if args.todate:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
        dkwargs['todate'] = todate

    if args.no_replay:
        data = bt.feeds.YahooFinanceCSVData(dataname=args.data,
                                            timeframe=bt.TimeFrame.Days,
                                            compression=1,
                                            **dkwargs)
        data.addfilter(DayStepsCloseFilter)
        cerebro.adddata(data)
    else:
        data = bt.feeds.YahooFinanceCSVData(dataname=args.data,
                                            timeframe=bt.TimeFrame.Minutes,
                                            compression=1,
                                            **dkwargs)
        data.addfilter(DayStepsReplayFilter)
        cerebro.replaydata(data, timeframe=bt.TimeFrame.Days, compression=1)

    cerebro.addstrategy(St,
                        sellafter=args.sellafter,
                        highperiod=args.highperiod,
                        market=args.market)

    cerebro.run(runonce=False, preload=False, oldbuysell=args.oldbuysell)
    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pinkfish challenge')

    parser.add_argument('--data', required=False,
                        default='../../datas/yhoo-1996-2015.txt',
                        help='Data to be read in')

    parser.add_argument('--fromdate', required=False,
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,
                        default='2006-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store',
                        type=float, default=50000,
                        help=('Cash to start with'))

    parser.add_argument('--sellafter', required=False, action='store',
                        type=int, default=2,
                        help=('Sell after so many bars in market'))

    parser.add_argument('--highperiod', required=False, action='store',
                        type=int, default=20,
                        help=('Period to look for the highest'))

    parser.add_argument('--no-replay', required=False, action='store_true',
                        help=('Use Replay + replay filter'))

    parser.add_argument('--market', required=False, action='store_true',
                        help=('Use Market exec instead of Close'))

    parser.add_argument('--oldbuysell', required=False, action='store_true',
                        help=('Old buysell plot behavior - ON THE PRICE'))

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example (escape the quotes if needed):\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
