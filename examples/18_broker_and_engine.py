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
"""More of the broker and the engine.

- Short selling: selling what is not held opens a short position, and a
  borrow rate (``interest``) is charged for every day it stays open.
- Deposits mid-run: ``add_cash`` changes the portfolio's value without
  being a profit. In fund mode (``set_fundmode``) the returns are measured
  per fund share, as a fund's would be, so the deposit does not count as
  performance.
- Cheat-on-open: with ``cheat_on_open=True`` the strategy also gets
  ``next_open()``, called once the new bar's open is known but before the
  broker executes. An order sent there fills at that open, and can be sized
  from it: here, buying 2,000,000 worth of stock the morning the index
  opened 0.55% lower (2006-08-10). Sized from the
  previous close instead, the order misses by however far the price
  gapped overnight. ``next_open`` must use only the open: the rest of the
  bar has not happened yet.
- The writer: ``addwriter`` records every bar's data, indicators and
  observers as CSV, for analysis outside backtrader.

Run it:  python examples/18_broker_and_engine.py [--plot]
"""

import io
import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"
FILE = str(DATAS / "2006-day-001.txt")


class ShortAndDeposit(bt.Strategy):
    def next(self):
        if len(self) == 1:
            self.sell(size=10)  # nothing held: this opens a short
        elif len(self) == 100:
            self.close()
        elif len(self) == 150:
            self.broker.add_cash(50_000.0)  # a deposit, not a profit


class BuyTwoMillion(bt.Strategy):
    """Buys 2,000,000 worth at the 2006-08-10 open, sized from that open when
    cheating on the open, from the 2006-08-09 close otherwise."""

    BAR = 155  # len(self) on 2006-08-09; next_open sees it with 08-10's open

    def __init__(self):
        self.fills = []

    def next_open(self):
        if len(self) == self.BAR:
            self.order_target_value(target=2_000_000.0, price=self.data.open[0])

    def next(self):
        if len(self) == self.BAR and not self.cerebro.p.cheat_on_open:
            self.order_target_value(target=2_000_000.0)

    def notify_order(self, order):
        if order.status == order.Completed:
            o = order.executed
            self.fills.append((self.data.datetime.date(0), o.size, o.price))


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(bt.feeds.BacktraderCSVData(dataname=FILE))
    cerebro.addstrategy(ShortAndDeposit)
    cerebro.broker.setcash(100_000.0)
    cerebro.broker.setcommission(interest=0.05)  # 5% a year to borrow
    cerebro.broker.set_fundmode(True)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="fund", fund=True)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="value", fund=False)
    strat = cerebro.run()[0]
    fund = sum(strat.analyzers.fund.get_analysis().values())
    value = cerebro.broker.getvalue()
    print(f"short 10 for 100 days at 5% interest, then a 50,000 deposit:")
    print(
        f"  final value {value:,.2f}; value-based returns, summed: "
        f"{sum(strat.analyzers.value.get_analysis().values()):+.2%}; "
        f"fund-share returns, summed: {fund:+.2%}"
    )
    if plot:
        cerebro.plot()

    for cheat in (False, True):
        cerebro = bt.Cerebro(stdstats=False, cheat_on_open=cheat)
        cerebro.adddata(bt.feeds.BacktraderCSVData(dataname=FILE))
        cerebro.addstrategy(BuyTwoMillion)
        cerebro.broker.setcash(3_000_000.0)
        strat = cerebro.run()[0]
        day, size, price = strat.fills[0]
        print(
            f"cheat_on_open={cheat!s:5s}: bought {size:.0f} on {day} at "
            f"{price:.2f} = {size * price:,.2f}"
        )

    out = io.StringIO()
    cerebro = bt.Cerebro()
    cerebro.adddata(bt.feeds.BacktraderCSVData(dataname=FILE))
    cerebro.addstrategy(ShortAndDeposit)
    cerebro.addwriter(bt.WriterFile, out=out, csv=True)
    cerebro.run()
    rows = [line for line in out.getvalue().splitlines() if line.count(",") > 5]
    print(f"writer: {len(rows)} CSV rows; the header starts {rows[0][:60]}...")


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
