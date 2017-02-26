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
    def __init__(self):
        self._host = args.host if args.host else 'localhost'
        self._port = args.port if args.port else 8086
        self._username = args.username if args.username else None
        self._password = args.password if args.password else None
        self._database = args.database if args.database else 'instruments'
        self._ticker = args.ticker
        self._cache = os.path.expanduser(args.sourcepath)

        self.dfdb = dfclient(self._host, self._port,
                             self._username, self._password,
                             self._database)

    def write_dataframe_to_idb(self, ticker):
        """Write Pandas Dataframe to InfluxDB database"""
        cachepath = self._cache
        cachefile = ('%s/%s-1M.csv.gz' % (cachepath, ticker))

        if not os.path.exists(cachefile):
            log.warn('Import file does not exist: %s' %
                     (cachefile))
            return

        df = pd.read_csv(cachefile, compression='infer', header=0,
                         infer_datetime_format=True)

        df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        df = df.set_index('Datetime')
        df = df.drop(['Date', 'Time'], axis=1)

        try:
            self.dfdb.write_points(df, ticker)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Run InfluxDB Import")

    exoptgroup = parser.add_mutually_exclusive_group(required=False)
    exoptgroup.add_argument("--ticker",
                            action='store', default='SPY',
                            help="Ticker to request data for.")
    exoptgroup.add_argument('--ticker-list',
                            action='store', default=None,
                            help='Path to folder to create files.')
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
                        default='~/.iqfeed/data',
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

    tool = InfluxDBTool()

    log = logging.getLogger()
    log_console = logging.StreamHandler(sys.stdout)
    log.addHandler(log_console)

    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.info:
        log.setLevel(logging.INFO)

    tickers = []
    if args.ticker_list:
        tickers = tool.get_tickers_from_file(args.ticker_list)
    else:
        tickers.append(args.ticker.rstrip())

    for (i, ticker) in enumerate(tickers):
        log.info("Processing %s (%d out of %d)", ticker, i+1,
                 len(tickers))
        tool.write_dataframe_to_idb(ticker=ticker)
