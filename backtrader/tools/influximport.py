#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

import sys
import os
import io
import logging
import argparse
import pandas as pd
from influxdb import DataFrameClient as dfclient
from influxdb.exceptions import InfluxDBClientError

class InfluxDBTool(object):
    def __init__(self, args):
        self._host = args.host if args.host else 'localhost'
        self._port = args.port if args.port else 8086
        self._username = args.username if args.username else None
        self._password = args.password if args.password else None
        self._database = args.database if args.database else 'instruments'
        self._sourcepath = os.path.expanduser(args.sourcepath)

        self.dfdb = dfclient(self._host, self._port,
                             self._username, self._password,
                             self._database, timeout=15)

    def write_dataframe_to_idb(self, t):
        """Write Pandas Dataframe to InfluxDB database"""

        ticker, tickerpath = t.split(":")
        if tickerpath is None:
            tickerpath = ticker

        sourcepath = self._sourcepath
        sourcefile = ('%s/%s' % (sourcepath, tickerpath))

        if not os.path.exists(sourcefile):
            log.warn('Import file does not exist: %s' %
                     (sourcefile))
            return

        df = pd.read_csv(sourcefile, header=0, infer_datetime_format=True, index_col=0, parse_dates=True)
        
        # cleanup data for import
        # lowercase on import for consistency and drop 'Adj Close if data coming from Yahoo'
        df.columns = [x.lower() for x in df.columns]
        if 'adj close' in df.columns:
            df.drop('adj close', axis=1, inplace=True)
        df[['high', 'low', 'open', 'close']] = df[['high', 'low', 'open', 'close']].astype(float)
        df['volume'] = df['volume'].astype(int)

        if 'openinterest' in df.columns:
            df['openinterest'] = df['openinterest'].astype(int)

        # handle separate time column if necessary
        if 'time' in df.columns:
            df['datetime'] = pd.to_datetime(df.index + ' ' + df['time'])
            df = df.set_index('datetime')
            df.drop('time', axis=1, inplace=True)

        df.dropna(inplace=True)

        try:
            self.dfdb.write_points(df, ticker, batch_size=100000)
        except InfluxDBClientError as err:
            log.error('Write to database failed: %s' % err)

    def get_tickers_from_file(self, filename):
        """Load ticker list from txt file"""
        if not os.path.exists(filename):
            log.error("Ticker List file does not exist: %s", filename)

        tickers = []
        with io.open(filename, 'r') as fd:
            for ticker in fd:
                tickers.append(ticker.rstrip())
        return tickers


def influximport():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Run InfluxDB Import")

    exoptgroup = parser.add_mutually_exclusive_group(required=True)
    exoptgroup.add_argument("--ticker",
                            action='store', default=None,
                            help="Ticker to load data for followed by file to load data from. E.g. SPY:SPY.csv")
    exoptgroup.add_argument('--ticker-file',
                            action='store', default=None,
                            help='List of tickers to load. Same format as for individual tickers')
    parser.add_argument('--host',
                        required=False, action='store',
                        default=None,
                        help='InfluxDB hostname.')
    parser.add_argument('--port',
                        required=False, action='store',
                        default=None, type=int,
                        help='InfluxDB port number.')
    parser.add_argument('--username',
                        required=False, action='store',
                        default=None,
                        help='InfluxDB username.')
    parser.add_argument('--password',
                        required=False, action='store',
                        default=None,
                        help='InfluxDB password.')
    parser.add_argument('--database',
                        required=False, action='store',
                        default=None,
                        help='InfluxDB database to use.')
    parser.add_argument('--sourcepath',
                        required=False, action='store',
                        default='.',
                        help='Path to CSV source folder.')
    parser.add_argument('--testrun',
                        required=False, action='store_true',
                        help='Don\'t write to InfluxDB')
    parser.add_argument('--debug',
                        required=False, action='store_true',
                        help='Turn on debug logging level.')
    parser.add_argument('--info',
                        required=False, action='store_true',
                        help='Turn on info logging level.')

    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        parser.exit(1)

    tool = InfluxDBTool(args)

    log = logging.getLogger()
    log_console = logging.StreamHandler(sys.stdout)
    log.addHandler(log_console)

    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.info:
        log.setLevel(logging.INFO)

    tickers = []
    if args.ticker_file:
        tickers = tool.get_tickers_from_file(args.ticker_file)
    else:
        tickers.append(args.ticker.rstrip())

    for (i, ticker) in enumerate(tickers):
        log.info("Processing %s (%d out of %d)", ticker, i+1,
                 len(tickers))
        tool.write_dataframe_to_idb(ticker)
