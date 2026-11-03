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
"""Several timeframes in one strategy, and replaying bars as they form.

- ``resampledata`` adds a coarser view of a feed. The strategy then sees
  ``data0`` (daily) and ``data1`` (weekly), each with its own indicators,
  and the weekly bar only changes once the week is complete.
- ``replaydata`` instead delivers the weekly bar while it is still forming:
  ``next()`` runs every day, and the current week's bar grows until Friday.
  That is how a strategy sees a live market build a bar.

Run it:  python examples/13_timeframes_and_replay.py [--plot]
"""

import datetime
import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"
FILE = str(DATAS / "2006-day-001.txt")


class TrendFilter(bt.Strategy):
    """Trades daily crossings, but only in the direction of the weekly trend."""

    def __init__(self):
        self.daily_cross = bt.ind.CrossOver(
            self.data0.close, bt.ind.SMA(self.data0, period=10)
        )
        self.weekly_up = self.data1.close > bt.ind.SMA(self.data1, period=10)

    def next(self):
        if not self.position and self.daily_cross[0] > 0 and self.weekly_up[0]:
            self.buy(data=self.data0, size=10)
        elif self.position and self.daily_cross[0] < 0:
            self.close(data=self.data0)


class WatchReplay(bt.Strategy):
    """Prints the weekly bar as it forms during one week."""

    def next(self):
        if (
            datetime.date(2006, 3, 6)
            <= self.data.datetime.date(0)
            <= datetime.date(2006, 3, 10)
        ):
            d = self.data
            print(
                f"  {d.datetime.date(0)} bar {len(d):2d}: open {d.open[0]:.2f} "
                f"high {d.high[0]:.2f} low {d.low[0]:.2f} close {d.close[0]:.2f}"
            )


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    daily = bt.feeds.BacktraderCSVData(dataname=FILE)
    cerebro.adddata(daily)
    cerebro.resampledata(daily, timeframe=bt.TimeFrame.Weeks)
    cerebro.addstrategy(TrendFilter)
    cerebro.broker.setcash(100_000.0)
    cerebro.run()
    print(
        f"daily entries, weekly filter: profit {cerebro.broker.getvalue() - 100_000:.2f}"
    )
    if plot:
        cerebro.plot()

    print("the week of 2006-03-06, replayed day by day as one weekly bar:")
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.replaydata(
        bt.feeds.BacktraderCSVData(dataname=FILE), timeframe=bt.TimeFrame.Weeks
    )
    cerebro.addstrategy(WatchReplay)
    cerebro.run(runonce=False)


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
