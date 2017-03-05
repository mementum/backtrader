#!/usr/bin/env python3
# -*- coding: utf-8; py-indent-offset:4 -*-

import sys
import os
import io
import socket
import logging
import numpy as np
import pandas as pd
import datetime as dt
import argparse
from influxdb import DataFrameClient as dfclient
from influxdb.exceptions import InfluxDBClientError


class IQFeedTool(object):
    def __init__(self):
        timeout = 10.0
        self._dbhost = args.dbhost if args.dbhost else 'localhost'
        self._dbport = args.dbport if args.dbport else 8086
        self._username = args.username if args.username else None
        self._password = args.password if args.password else None
        self._database = args.database if args.database else 'instruments'
        self._ticker = args.ticker

        self._iqhost = args.iqhost if args.iqhost else 'localhost'
        self._iqport = args.iqport if args.iqport else 9100
        self._ticker = args.ticker
        self._year = None
        self._recv_buf = ""
        self._ndf = pd.DataFrame()

        # Open a streaming socket to the IQFeed daemon
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._iqhost, self._iqport))
        self._sock.settimeout(timeout)

        self.dfdb = dfclient(self._dbhost, self._dbport,
                             self._username, self._password,
                             self._database)

        if not args.fromdate:
            self._start = str(dt.datetime.today().year)
        elif len(args.fromdate) == 4 or len(args.fromdate == 10):
            self._start = args.fromdate
        else:
            log.error('Starting date required in YYYY-MM-DD or YYYY format.')
            sys.exit(-1)

        if not args.todate:
            self._stop = str(dt.datetime.today().year)
        elif len(args.fromdate) == 4 or len(args.fromdate == 10):
            self._stop = args.todate
        else:
            log.error('Starting date required in YYYY-MM-DD or YYYY format.')
            sys.exit(-1)

    def _send_cmd(self, cmd: str):
        """Encode IQFeed API messages."""
        self._sock.sendall(cmd.encode(encoding='latin-1', errors='strict'))

    def iq_query(self, message: str):
        """Send data query to IQFeed API."""
        end_msg = '!ENDMSG!'
        recv_buffer = 4096

        # Send the historical data request message and buffer the data
        self._send_cmd(message)

        chunk = ""
        data = ""
        while True:
            chunk = self._sock.recv(recv_buffer).decode('latin-1')
            data += chunk
            if chunk.startswith('E,'):  # error condition
                if chunk.startswith('E,!NO_DATA!'):
                    log.warn('No data available for the given symbol or dates')
                    return
                else:
                    raise Exception(chunk)
            elif end_msg in chunk:
                break

        # Clean up the data.
        data = data[:-1 * (len(end_msg) + 3)]
        data = "".join(data.split("\r"))
        data = data.replace(",\n", ",")[:-1]
        data = data.split(",")
        return data

    def get_historical_minute_data(self, ticker: str):
        """Request historical 5 minute data from DTN."""
        start = self._start
        stop = self._stop

        if len(stop) > 4:
            stop = stop[:4]

        if len(start) > 4:
            start = start[:4]

        for year in range(int(start), int(stop) + 1):
            beg_time = ('%s0101000000' % year)
            end_time = ('%s1231235959' % year)
            msg = "HIT,%s,60,%s,%s,,,,1,,,s\r\n" % (ticker,
                                                    beg_time,
                                                    end_time)
            try:
                data = iq.iq_query(message=msg)
                iq.add_data_to_df(data=data)
            except Exception as err:
                log.error('No data returned because %s', err)

        try:
            self.dfdb.write_points(self._ndf, ticker)
        except InfluxDBClientError as err:
            log.error('Write to database failed: %s' % err)

    def add_data_to_df(self, data: np.array):
        """Build Pandas Dataframe in memory"""

        col_names = ['high_p', 'low_p', 'open_p', 'close_p', 'volume', 'oi']

        data = np.array(data).reshape(-1, len(col_names) + 1)
        df = pd.DataFrame(data=data[:, 1:], index=data[:, 0],
                          columns=col_names)

        df.index = pd.to_datetime(df.index)

        # Sort the dataframe based on ascending dates.
        df.sort_index(ascending=True, inplace=True)

        # Convert dataframe columns to float and ints.
        df[['high_p', 'low_p', 'open_p', 'close_p']] = df[
            ['high_p', 'low_p', 'open_p', 'close_p']].astype(float)
        df[['volume', 'oi']] = df[['volume', 'oi']].astype(int)

        if self._ndf.empty:
            self._ndf = df
        else:
            self._ndf = self._ndf.append(df)

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
        description="Import IQFeed Historical Data to InfluxDB")

    exoptgroup = parser.add_mutually_exclusive_group(required=True)
    exoptgroup.add_argument("--ticker",
                            action='store', default='SPY',
                            help="Ticker to request data for.")
    exoptgroup.add_argument('--ticker-list',
                            action='store', default=None,
                            help='Path to folder to create files.')
    parser.add_argument('--dbhost',
                        required=False, action='store',
                        default=None,
                        help='InfluxDB hostname.')
    parser.add_argument('--dbport',
                        required=False, action='store',
                        default=None, type=int,
                        help='InfluxDB port number.')
    parser.add_argument('--iqhost',
                        required=False, action='store',
                        default=None,
                        help='IQfeed Connect hostname.')
    parser.add_argument('--iqport',
                        required=False, action='store',
                        default=None, type=int,
                        help='IQfeed Connect port number.')
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
    parser.add_argument('--fromdate',
                        required=False, action='store', default=None,
                        type=str,
                        help=('Starting date for historical download '
                              'with format: YYYY[-MM-DDTHH:MM:SS].'))
    parser.add_argument('--todate',
                        required=False, action='store', default=None,
                        type=str,
                        help=('Ending date for historical download '
                              'with format: YYYY[-MM-DDTHH:MM:SS].'))
    parser.add_argument('--debug',
                        required=False, action='store_true',
                        help='Turn on debug logging level.')
    parser.add_argument('--info',
                        required=False, action='store_true',
                        help='Turn on info logging level.')

    args = parser.parse_args()

    iq = IQFeedTool()

    log = logging.getLogger()
    log_console = logging.StreamHandler(sys.stdout)
    log.addHandler(log_console)

    tickers = []
    if args.ticker_list:
        tickers = iq.get_tickers_from_file(args.ticker_list)
    else:
        tickers.append(args.ticker.rstrip())

    for (i, ticker) in enumerate(tickers):
        try:
            log.info("Processing %s (%d out of %d)", ticker, i+1,
                     len(tickers))

            iq.get_historical_minute_data(ticker=ticker)

        except Exception as err:
            log.error('Error returned: %s', err)
