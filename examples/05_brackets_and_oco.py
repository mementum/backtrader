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
"""Orders that manage each other: brackets and one-cancels-other.

- ``buy_bracket`` sends three orders: an entry, a stop-loss below it and a
  take-profit above it. The exits are only active once the entry fills, and
  whichever exit fills first cancels the other.
- ``oco=`` links orders so that the first to fill (or be cancelled) cancels
  the rest: here, two entry limits at different prices, only one of which
  may trade.

Run it:  python examples/05_brackets_and_oco.py [--plot]
"""

import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class Brackets(bt.Strategy):
    def __init__(self):
        self.pending = []
        self.entered = None

    def next(self):
        if self.pending:
            return
        if self.position:
            # an oco entry has no exits attached: leave after 10 bars
            if self.label == "oco" and len(self) - self.entered >= 10:
                self.close()
            return
        close = self.data.close[0]
        if len(self) % 2:
            # entry at the market, -2% stop-loss, +3% take-profit
            self.pending = self.buy_bracket(
                size=10,
                exectype=bt.Order.Market,
                stopprice=close * 0.98,
                limitprice=close * 1.03,
            )
            self.label = "bracket"
        else:
            # two entries, of which only the first to fill survives
            first = self.buy(size=10, exectype=bt.Order.Limit, price=close * 0.995)
            second = self.buy(
                size=10, exectype=bt.Order.Limit, price=close * 0.99, oco=first
            )
            self.pending = [first, second]
            self.label = "oco"

    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            return
        when = self.data.datetime.date(0)
        if order.status == order.Completed:
            if order.isbuy():
                self.entered = len(self)
            side = "buy " if order.isbuy() else "sell"
            print(f"{when} {self.label:7s} {side} at {order.executed.price:8.2f}")
        else:
            print(f"{when} {self.label:7s} order {order.ref} {order.getstatusname()}")
        if not order.alive() and order in self.pending:
            self.pending.remove(order)

    def notify_trade(self, trade):
        if trade.isclosed:
            print(f"{self.data.datetime.date(0)} trade closed: {trade.pnl:+.2f}")


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(
        bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    )
    cerebro.addstrategy(Brackets)
    cerebro.broker.setcash(100_000.0)
    cerebro.run()
    print(f"final value {cerebro.broker.getvalue():,.2f}")
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
