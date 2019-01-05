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
import collections
import datetime
import io
import logging
import sys
import itertools

import backtrader as bt

TIMEFRAMES = dict(
    seconds=bt.TimeFrame.Seconds,
    minutes=bt.TimeFrame.Minutes,
    days=bt.TimeFrame.Days,
    weeks=bt.TimeFrame.Weeks,
    months=bt.TimeFrame.Months,
    years=bt.TimeFrame.Years,
)

logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging.INFO)

class DownloadStrategy(bt.Strategy):
    params = (
        ('separator', ','),
        ('outfile', None),
    )

    def start(self):
        if self.p.outfile is None:
            self.f = sys.stdout
        else:
            self.f = open(self.p.outfile, 'w')
            logging.info('opened file {}'.format(self.p.outfile))

        headers = 'date,open,high,low,close,volume,openinterest\n'
        self.f.write(headers)

    def stop(self):
        if self.p.outfile:
            logging.info('closing file {}'.format(self.p.outfile))
            self.f.close()

    def next(self):
        fields = list()
        if self.data._timeframe < bt.TimeFrame.Days:
            dt = self.data.datetime.date(0).strftime('%Y-%m-%d')
            tm = self.data.datetime.time(0).strftime('%H:%M:%S')
            fields.append('{} {}'.format(dt, tm))
        else:
            dt = self.data.datetime.date(0).strftime('%Y-%m-%d')
            fields.append(dt)

        o = self.data.open[0]
        fields.append(o)
        h = self.data.high[0]
        fields.append(h)
        l = self.data.low[0]
        fields.append(l)
        c = self.data.close[0]
        fields.append(c)
        v = int(self.data.volume[0])
        fields.append(v)
        oi = int(self.data.openinterest[0])
        fields.append(oi)

        txt = self.p.separator.join(str(x) for x in fields)
        txt += '\n'
        self.f.write(txt)

def ibdownload():
    args = parse_args()

    logging.debug('Processing input parameters')
    logging.debug('Processing fromdate')
    try:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    except Exception as e:
        logging.error('Converting fromdate failed')
        logging.error(str(e))
        sys.exit(1)

    logging.debug('Processing todate')
    todate = datetime.datetime.today()
    if args.todate:
        try:
            todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
        except Exception as e:
            logging.error('Converting todate failed')
            logging.error(str(e))
            sys.exit(1)

    outfile = '{}_{}-{}-{}.csv'.format(args.timeframe[0].capitalize(), args.ticker, fromdate.strftime('%Y-%m-%d'), todate.strftime('%Y-%m-%d'))
    if args.outfile:
        outfile = args.outfile

    logging.info('Downloading from IB')
    try:
        cerebro = bt.Cerebro(tz=0)
        ibstore = bt.stores.IBStore(host=str(args.host), port=int(args.port), clientId=int(args.client), reconnect=1)
        data = ibstore.getdata(dataname=args.ticker, timeframe=TIMEFRAMES[args.timeframe], 
            compression=int(args.compression), historical=True, useRTH=args.userth, fromdate=fromdate, todate=todate)

        cerebro.adddata(data)

        cerebro.addstrategy(DownloadStrategy, outfile=outfile)
        cerebro.run(stdstats=False)

    except Exception as e:
        logging.error('Downloading data from IB failed')
        logging.error(str(e))
        sys.exit(1)

    logging.info('All operations completed successfully')
    sys.exit(0)

# - TICKER  # Stock type and SMART exchange
# - TICKER-STK  # Stock and SMART exchange
# - TICKER-STK-EXCHANGE  # Stock
# - TICKER-STK-EXCHANGE-CURRENCY  # Stock

# - TICKER-CFD  # CFD and SMART exchange
# - TICKER-CFD-EXCHANGE  # CFD
# - TICKER-CDF-EXCHANGE-CURRENCY  # Stock

# - TICKER-IND-EXCHANGE  # Index
# - TICKER-IND-EXCHANGE-CURRENCY  # Index

# - TICKER-YYYYMM-EXCHANGE  # Future
# - TICKER-YYYYMM-EXCHANGE-CURRENCY  # Future
# - TICKER-YYYYMM-EXCHANGE-CURRENCY-MULT  # Future
# - TICKER-FUT-EXCHANGE-CURRENCY-YYYYMM-MULT # Future
# - TICKER-CONTFUT-EXCHANGE # Continuous Future (only for historical data)

# - TICKER-YYYYMM-EXCHANGE-CURRENCY-STRIKE-RIGHT  # FOP
# - TICKER-YYYYMM-EXCHANGE-CURRENCY-STRIKE-RIGHT-MULT  # FOP
# - TICKER-FOP-EXCHANGE-CURRENCY-YYYYMM-STRIKE-RIGHT # FOP
# - TICKER-FOP-EXCHANGE-CURRENCY-YYYYMM-STRIKE-RIGHT-MULT # FOP

# - CUR1.CUR2-CASH-IDEALPRO  # Forex

# - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-STRIKE-RIGHT  # OPT
# - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-STRIKE-RIGHT-MULT  # OPT
# - TICKER-OPT-EXCHANGE-CURRENCY-YYYYMMDD-STRIKE-RIGHT # OPT
# - TICKER-OPT-EXCHANGE-CURRENCY-YYYYMMDD-STRIKE-RIGHT-MULT # OPT
def parse_args():
    parser = argparse.ArgumentParser(
        description='Download IB Finance Data in CSV')

    parser.add_argument('--host', required=False, default='127.0.0.1',
                        help='IB gateway/tws host to download from')

    parser.add_argument('--port', required=False, default='7497',
                        help='IB gateway/tws port to download from')

    parser.add_argument('--client', required=False, default='25',
                        help='clientId to use when connecting to IB gateway/tws')  

    parser.add_argument('--ticker', required=True,
                        help='Ticker to be downloaded')

    parser.add_argument('--fromdate', required=True,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--timeframe', required=False, default='minutes',
                       choices=TIMEFRAMES.keys(),
                       help='What data resolution to use. Can be one of the above choices.')

    parser.add_argument('--compression', required=False, default=1,
                       type=int,
                       help='How to compress the data. Integer')

    rth_parser = parser.add_mutually_exclusive_group(required=False)
    rth_parser.add_argument('--rth', dest='userth', action='store_true')
    rth_parser.add_argument('--no-rth', dest='userth', action='store_false')
    parser.set_defaults(userth=True)

    parser.add_argument('--outfile', required=False, help='Output file name')

    return parser.parse_args()


