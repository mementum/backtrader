#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2026 Dennis Hansen
#
# This file is part of slim-backtrader, a modified version of backtrader
# (Copyright (C) 2015-2023 Daniel Rodriguez).
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
"""Getting data in: CSV files, column mappings, date ranges, timeframes.

- ``BacktraderCSVData`` reads backtrader's own CSV layout.
- ``GenericCSVData`` reads any CSV once told which column holds what.
- ``YahooFinanceCSVData`` reads Yahoo's download format, adjusting prices.
- ``fromdate``/``todate`` cut a feed to a window.
- ``resampledata`` turns daily bars into weekly ones; both can feed one
  strategy, each with its own indicators.
- A pandas DataFrame works too, through ``PandasData`` (if pandas is
  installed).

Run it:  python examples/02_data_feeds.py [--plot]
"""

import datetime
import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class Describe(bt.Strategy):
    """Prints what each feed looks like on its first and last bar."""

    def __init__(self):
        self.firsts = {}

    def prenext(self):
        # prenext runs while some feed has no bar yet (the weekly one needs a
        # week); next runs once all have one. This strategy does the same in
        # both.
        self.next()

    def next(self):
        for d in self.datas:
            if len(d) and d._name not in self.firsts:
                self.firsts[d._name] = (d.datetime.date(0), d.close[0])

    def stop(self):
        for d in self.datas:
            first_day, first_close = self.firsts[d._name]
            print(
                f"{d._name:10s} {len(d):4d} bars  "
                f"{first_day} close {first_close:9.2f} .. "
                f"{d.datetime.date(0)} close {d.close[0]:9.2f}"
            )


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)

    # 1. backtrader's own format: Date,Open,High,Low,Close,Volume,OpenInterest
    daily = bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    cerebro.adddata(daily, name="daily")

    # 2. the same daily bars, aggregated into weeks by the engine
    cerebro.resampledata(daily, timeframe=bt.TimeFrame.Weeks, name="weekly")

    # 3. any CSV: say which column is which (-1: not present)
    generic = bt.feeds.GenericCSVData(
        dataname=str(DATAS / "2006-day-002.txt"),
        dtformat="%Y-%m-%d",
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
    )
    cerebro.adddata(generic, name="generic")

    # 4. a Yahoo download, cut to the first half of the year. Prices are
    #    adjusted to the "Adj Close" column. Feeds need not overlap in time:
    #    cerebro lines every feed up by datetime
    yahoo = bt.feeds.YahooFinanceCSVData(
        dataname=str(DATAS / "orcl-2014.txt"),
        fromdate=datetime.datetime(2014, 1, 1),
        todate=datetime.datetime(2014, 6, 30),
    )
    cerebro.adddata(yahoo, name="orcl-h1")

    # 5. a pandas DataFrame, if pandas is available
    try:
        import pandas as pd
    except ImportError:
        print("(pandas not installed: skipping PandasData)")
    else:
        frame = pd.read_csv(
            DATAS / "2006-day-001.txt", parse_dates=["Date"], index_col="Date"
        )
        cerebro.adddata(bt.feeds.PandasData(dataname=frame), name="pandas")

    cerebro.addstrategy(Describe)
    cerebro.run()
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
