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

# The above could be sent to an independent module
import backtrader as bt
from backtrader.utils import flushfile  # win32 quick stdout flushing
from backtrader.utils.py3 import string_types


class TestStrategy(bt.Strategy):
    params = dict(
        smaperiod=5,
        trade=False,
        stake=10,
        exectype=bt.Order.Market,
        stopafter=0,
        valid=None,
        cancel=0,
        donotsell=False,
        price=None,
        pstoplimit=None,
    )

    def __init__(self):
        # To control operation entries
        self.orderid = list()
        self.order = None

        self.counttostop = 0
        self.datastatus = 0

        # Create SMA on 2nd data
        self.sma = bt.indicators.MovAv.SMA(self.data, period=self.p.smaperiod)

        print('--------------------------------------------------')
        print('Strategy Created')
        print('--------------------------------------------------')

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            self.counttostop = self.p.stopafter
            self.datastatus = 1

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF:', msg)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Cancelled, order.Rejected]:
            self.order = None

        print('-' * 50, 'ORDER BEGIN', datetime.datetime.now())
        print(order)
        print('-' * 50, 'ORDER END')

    def notify_trade(self, trade):
        print('-' * 50, 'TRADE BEGIN', datetime.datetime.now())
        print(trade)
        print('-' * 50, 'TRADE END')

    def prenext(self):
        self.next(frompre=True)

    def next(self, frompre=False):
        txt = list()
        txt.append('%04d' % len(self))
        dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
        txt.append('%s' % self.data.datetime.datetime(0).strftime(dtfmt))
        txt.append('{}'.format(self.data.open[0]))
        txt.append('{}'.format(self.data.high[0]))
        txt.append('{}'.format(self.data.low[0]))
        txt.append('{}'.format(self.data.close[0]))
        txt.append('{}'.format(self.data.volume[0]))
        txt.append('{}'.format(self.data.openinterest[0]))
        txt.append('{}'.format(self.sma[0]))
        print(', '.join(txt))

        if len(self.datas) > 1:
            txt = list()
            txt.append('%04d' % len(self))
            dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
            txt.append('%s' % self.data1.datetime.datetime(0).strftime(dtfmt))
            txt.append('{}'.format(self.data1.open[0]))
            txt.append('{}'.format(self.data1.high[0]))
            txt.append('{}'.format(self.data1.low[0]))
            txt.append('{}'.format(self.data1.close[0]))
            txt.append('{}'.format(self.data1.volume[0]))
            txt.append('{}'.format(self.data1.openinterest[0]))
            txt.append('{}'.format(float('NaN')))
            print(', '.join(txt))

        if self.counttostop:  # stop after x live lines
            self.counttostop -= 1
            if not self.counttostop:
                self.env.runstop()
                return

        if not self.p.trade:
            return

        # if True and len(self.orderid) < 1:
        if self.datastatus and not self.position and len(self.orderid) < 1:
            self.order = self.buy(size=self.p.stake,
                                  exectype=self.p.exectype,
                                  price=self.p.price,
                                  plimit=self.p.pstoplimit,
                                  valid=self.p.valid)

            self.orderid.append(self.order)
        elif self.position.size > 0 and not self.p.donotsell:
            if self.order is None:
                size = self.p.stake // 2
                if not size:
                    size = self.position.size  # use the remaining
                self.order = self.sell(size=size, exectype=bt.Order.Market)

        elif self.order is not None and self.p.cancel:
            if self.datastatus > self.p.cancel:
                self.cancel(self.order)

        if self.datastatus:
            self.datastatus += 1

    def start(self):
        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
                  'OpenInterest', 'SMA']
        print(', '.join(header))

        self.done = False


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    storekwargs = dict()

    if not args.nostore:
        vcstore = bt.stores.VCStore(**storekwargs)

    if args.broker:
        brokerargs = dict(account=args.account, **storekwargs)
        if not args.nostore:
            broker = vcstore.getbroker(**brokerargs)
        else:
            broker = bt.brokers.VCBroker(**brokerargs)

        cerebro.setbroker(broker)

    timeframe = bt.TimeFrame.TFrame(args.timeframe)
    if args.resample or args.replay:
        datatf = bt.TimeFrame.Ticks
        datacomp = 1
    else:
        datatf = timeframe
        datacomp = args.compression

    fromdate = None
    if args.fromdate:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in args.fromdate))
        fromdate = datetime.datetime.strptime(args.fromdate, dtformat)

    todate = None
    if args.todate:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in args.todate))
        todate = datetime.datetime.strptime(args.todate, dtformat)

    VCDataFactory = vcstore.getdata if not args.nostore else bt.feeds.VCData

    datakwargs = dict(
        timeframe=datatf, compression=datacomp,
        fromdate=fromdate, todate=todate,
        historical=args.historical,
        qcheck=args.qcheck,
        tz=args.timezone
    )

    if args.nostore and not args.broker:   # neither store nor broker
        datakwargs.update(storekwargs)  # pass the store args over the data

    data0 = VCDataFactory(dataname=args.data0, tradename=args.tradename,
                          **datakwargs)

    data1 = None
    if args.data1 is not None:
        data1 = VCDataFactory(dataname=args.data1, **datakwargs)

    rekwargs = dict(
        timeframe=timeframe, compression=args.compression,
        bar2edge=not args.no_bar2edge,
        adjbartime=not args.no_adjbartime,
        rightedge=not args.no_rightedge,
    )

    if args.replay:
        cerebro.replaydata(data0, **rekwargs)

        if data1 is not None:
            cerebro.replaydata(data1, **rekwargs)

    elif args.resample:
        cerebro.resampledata(data0, **rekwargs)

        if data1 is not None:
            cerebro.resampledata(data1, **rekwargs)

    else:
        cerebro.adddata(data0)
        if data1 is not None:
            cerebro.adddata(data1)

    if args.valid is None:
        valid = None
    else:
        try:
            valid = float(args.valid)
        except:
            dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in args.valid))
            valid = datetime.datetime.strptime(args.valid, dtformat)
        else:
            valid = datetime.timedelta(seconds=args.valid)

    # Add the strategy
    cerebro.addstrategy(TestStrategy,
                        smaperiod=args.smaperiod,
                        trade=args.trade,
                        exectype=bt.Order.ExecType(args.exectype),
                        stake=args.stake,
                        stopafter=args.stopafter,
                        valid=valid,
                        cancel=args.cancel,
                        donotsell=args.donotsell,
                        price=args.price,
                        pstoplimit=args.pstoplimit)

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars=args.exactbars)

    if args.plot and args.exactbars < 1:  # plot if possible
        cerebro.plot()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Test Visual Chart 6 integration')

    parser.add_argument('--exactbars', default=1, type=int,
                        required=False, action='store',
                        help='exactbars level, use 0/-1/-2 to enable plotting')

    parser.add_argument('--plot',
                        required=False, action='store_true',
                        help='Plot if possible')

    parser.add_argument('--stopafter', default=0, type=int,
                        required=False, action='store',
                        help='Stop after x lines of LIVE data')

    parser.add_argument('--nostore',
                        required=False, action='store_true',
                        help='Do not Use the store pattern')

    parser.add_argument('--qcheck', default=0.5, type=float,
                        required=False, action='store',
                        help=('Timeout for periodic '
                              'notification/resampling/replaying check'))

    parser.add_argument('--no-timeoffset',
                        required=False, action='store_true',
                        help=('Do not Use TWS/System time offset for non '
                              'timestamped prices and to align resampling'))

    parser.add_argument('--data0', default=None,
                        required=True, action='store',
                        help='data 0 into the system')

    parser.add_argument('--tradename', default=None,
                        required=False, action='store',
                        help='Actual Trading Name of the asset')

    parser.add_argument('--data1', default=None,
                        required=False, action='store',
                        help='data 1 into the system')

    parser.add_argument('--timezone', default=None,
                        required=False, action='store',
                        help='timezone to get time output into (pytz names)')

    parser.add_argument('--historical',
                        required=False, action='store_true',
                        help='do only historical download')

    parser.add_argument('--fromdate',
                        required=False, action='store',
                        help=('Starting date for historical download '
                              'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--todate',
                        required=False, action='store',
                        help=('End date for historical download '
                              'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--smaperiod', default=5, type=int,
                        required=False, action='store',
                        help='Period to apply to the Simple Moving Average')

    pgroup = parser.add_mutually_exclusive_group(required=False)

    pgroup.add_argument('--replay',
                        required=False, action='store_true',
                        help='replay to chosen timeframe')

    pgroup.add_argument('--resample',
                        required=False, action='store_true',
                        help='resample to chosen timeframe')

    parser.add_argument('--timeframe', default=bt.TimeFrame.Names[0],
                        choices=bt.TimeFrame.Names,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay')

    parser.add_argument('--compression', default=1, type=int,
                        required=False, action='store',
                        help='Compression for Resample/Replay')

    parser.add_argument('--no-bar2edge',
                        required=False, action='store_true',
                        help='no bar2edge for resample/replay')

    parser.add_argument('--no-adjbartime',
                        required=False, action='store_true',
                        help='no adjbartime for resample/replay')

    parser.add_argument('--no-rightedge',
                        required=False, action='store_true',
                        help='no rightedge for resample/replay')

    parser.add_argument('--broker',
                        required=False, action='store_true',
                        help='Use VisualChart as broker')

    parser.add_argument('--account', default=None,
                        required=False, action='store',
                        help='Choose broker account (else first)')

    parser.add_argument('--trade',
                        required=False, action='store_true',
                        help='Do Sample Buy/Sell operations')

    parser.add_argument('--donotsell',
                        required=False, action='store_true',
                        help='Do not sell after a buy')

    parser.add_argument('--exectype', default=bt.Order.ExecTypes[0],
                        choices=bt.Order.ExecTypes,
                        required=False, action='store',
                        help='Execution to Use when opening position')

    parser.add_argument('--price', default=None, type=float,
                        required=False, action='store',
                        help='Price in Limit orders or Stop Trigger Price')

    parser.add_argument('--pstoplimit', default=None, type=float,
                        required=False, action='store',
                        help='Price for the limit in StopLimit')

    parser.add_argument('--stake', default=10, type=int,
                        required=False, action='store',
                        help='Stake to use in buy operations')

    parser.add_argument('--valid', default=None,
                        required=False, action='store',
                        help='Seconds or YYYY-MM-DD')

    parser.add_argument('--cancel', default=0, type=int,
                        required=False, action='store',
                        help=('Cancel a buy order after n bars in operation,'
                              ' to be combined with orders like Limit'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
