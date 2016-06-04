#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015,2016 Daniel Rodriguez
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
import backtrader.feeds as btfeeds
import backtrader.brokers as btbrokers
import backtrader.indicators as btind
from backtrader.utils import flushfile


class EmptyStrategy(bt.Strategy):
    params = dict(
        smaperiod=5,
        trade=False,
        stake=10,
        exectype=bt.Order.Market,
    )

    def __init__(self):
        # To control operation entries
        self.orderid = list()
        self.order = None

        # Create SMA on 2nd data
        self.sma = btind.MovAv.SMA(self.data, period=self.p.smaperiod)

        print('--------------------------------------------------')
        print('Strategy Created')
        print('--------------------------------------------------')

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status))

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF:', msg)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Cancelled, order.Rejected]:
            self.order = None

        print('-' * 50, 'ORDER BEGIN')
        print(order)
        print('-' * 50, 'ORDER END')

    def notify_trade(self, trade):
        print('-' * 50, 'TRADE BEGIN')
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

        # print('Position size is:', self.position.size)
        if not self.p.trade:
            return

        if not self.position and len(self.orderid) < 1:
            self.order = self.buy(size=self.p.stake,
                                  exectype=self.p.exectype,
                                  price=round(self.data0.close[0] * 0.90, 2),
                                  # valid=self.data0.datetime[0] + 2.0)
                                  # valid=0)
                                  valid=datetime.timedelta())
            self.orderid.append(self.order)
        elif self.position.size > 0:
            if self.order is None:
                self.order = self.sell(size=self.p.stake // 2,
                                       exectype=bt.Order.Market,
                                       price=self.data0.close[0])

    def start(self):
        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
                  'OpenInterest', 'SMA']
        print(', '.join(header))

        self.done = False


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    if args.broker:
        b = btbrokers.IBBroker(port=args.port, _debug=args.debug)
        cerebro.setbroker(b)

    timeframe = bt.TimeFrame.TFrame(args.timeframe.capitalize())
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

    data0 = btfeeds.IBData(dataname=args.data0,
                           port=args.port,
                           useRT=args.rtbar,
                           _debug=args.debug,
                           notifyall=args.notifyall,
                           fromdate=fromdate,
                           historical=args.historical,
                           timeframe=datatf,
                           compression=datacomp)

    if args.data1 is None:
        data1 = None
    else:
        data1 = btfeeds.IBData(dataname='AAPL-STK-SMART-USD',
                               port=args.port,
                               useRT=args.rtbar,
                               _debug=args.debug,
                               notifyall=args.notifyall,
                               fromdate=fromdate,
                               historical=args.historical,
                               timeframe=datatf,
                               compression=datacomp)

    bar2edge = not args.nobar2edge
    adjbartime = not args.noadjbartime
    rightedge = not args.norightedge

    if args.replay:
        cerebro.replaydata(dataname=data0,
                           timeframe=timeframe,
                           compression=args.compression,
                           bar2edge=bar2edge,
                           adjbartime=adjbartime,
                           rightedge=rightedge)
        if data1 is not None:
            cerebro.replaydata(dataname=data1,
                               timeframe=timeframe,
                               compression=args.compression,
                               bar2edge=bar2edge,
                               adjbartime=adjbartime,
                               rightedge=rightedge)
    elif args.resample:
        cerebro.resampledata(dataname=data0,
                             timeframe=timeframe,
                             compression=args.compression,
                             bar2edge=bar2edge,
                             adjbartime=adjbartime,
                             rightedge=rightedge)

        if data1 is not None:
            cerebro.resampledata(dataname=data1,
                                 timeframe=timeframe,
                                 compression=args.compression,
                                 bar2edge=bar2edge,
                                 adjbartime=adjbartime,
                                 rightedge=rightedge)
    else:
        cerebro.adddata(data0)
        if data1 is not None:
            cerebro.adddata(data1)

    # Add the strategy
    cerebro.addstrategy(EmptyStrategy,
                        smaperiod=args.smaperiod,
                        trade=args.trade,
                        stake=args.stake,
                        exectype=bt.Order.ExecType(args.exectype))

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars=1)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Test IB Realtime Data Feed')

    parser.add_argument('--data0', required=False, default='IBKR',
                        help='data into the system')

    parser.add_argument('--data1', action='store', default=None,
                        help='data into the system')

    parser.add_argument('--port', default=7496, type=int,
                        help='Port for the Interactive Brokers TWS Connection')

    parser.add_argument('--rtbar', required=False, action='store_true',
                        help='Use 5 seconds real time bar updates')

    parser.add_argument('--debug', required=False, action='store_true',
                        help='Display all info received form IB')

    parser.add_argument('--seeprint', required=False, action='store_true',
                        help='See IbPy initial print messages')

    parser.add_argument('--smaperiod', default=5, type=int,
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--stake', default=10, type=int,
                        help='Stake to use')

    parser.add_argument('--trade', required=False, action='store_true',
                        help='Do Buy/Sell operations')

    parser.add_argument('--exectype', required=False, action='store',
                        default=bt.Order.ExecTypes[0],
                        choices=bt.Order.ExecTypes,
                        help='Execution to Use when opening position')

    pgroup = parser.add_mutually_exclusive_group(required=False)

    pgroup.add_argument('--replay', required=False, action='store_true',
                        help='replay to chosen timeframe')

    pgroup.add_argument('--resample', required=False, action='store_true',
                        help='resample to chosen timeframe')

    parser.add_argument('--historical', required=False, action='store_true',
                        help='do only historical download')

    parser.add_argument('--fromdate', required=False, action='store',
                        help=('Starting date for historical or backfilling '
                              'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--timeframe',
                        default=bt.TimeFrame.Names[0], required=False,
                        action='store', choices=bt.TimeFrame.Names,
                        help='TimeFrame')

    parser.add_argument('--compression', default=1, type=int,
                        help='Compression level')

    parser.add_argument('--nobar2edge', required=False, action='store_true',
                        help='no bar2edge')

    parser.add_argument('--noadjbartime', required=False, action='store_true',
                        help='noadjbartime')

    parser.add_argument('--norightedge', required=False, action='store_true',
                        help='rightedge')

    parser.add_argument('--broker', required=False, action='store_true',
                        help='Use IB as broker')

    parser.add_argument('--notifyall', required=False, action='store_true',
                        help='Notify all messages to strategy')
    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
