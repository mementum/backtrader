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
"""What trading costs: commission schemes, slippage and fill timing.

The same strategy - buy 10 units every 20 bars, sell them 10 bars later -
under different broker settings:

- no costs at all;
- a percentage commission (0.1% of the traded value), as for stocks;
- a fixed amount per unit traded;
- futures-style: a margin per contract, a multiplier, and the daily
  profit and loss settled in cash;
- slippage: every fill 0.1% worse than the price it would have had;
- cheat-on-close: market orders filled at the close of the bar on which
  they were sent, rather than the next open (look-ahead, for comparison
  only).

Run it:  python examples/07_commissions_and_slippage.py [--plot]
"""

import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class InAndOut(bt.Strategy):
    def __init__(self):
        self.costs = 0.0

    def next(self):
        if len(self) % 20 == 0:
            self.buy(size=10)
        elif len(self) % 20 == 10 and self.position:
            self.close()

    def notify_order(self, order):
        if order.status == order.Completed:
            self.costs += order.executed.comm


def run(label, setup, plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(
        bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    )
    cerebro.addstrategy(InAndOut)
    cerebro.broker.setcash(100_000.0)
    setup(cerebro.broker)
    strat = cerebro.run()[0]
    pnl = cerebro.broker.getvalue() - 100_000.0
    print(f"{label:28s} profit {pnl:10.2f}   commission paid {strat.costs:8.2f}")
    if plot:
        cerebro.plot()


def main(plot=False):
    run("no costs", lambda b: None)
    run("0.1% commission", lambda b: b.setcommission(commission=0.001), plot=plot)
    run(
        "2.00 per unit",
        lambda b: b.setcommission(
            commission=2.0, commtype=bt.CommInfoBase.COMM_FIXED, stocklike=True
        ),
    )
    run(
        "futures: margin 2000, x10",
        lambda b: b.setcommission(commission=2.0, margin=2000.0, mult=10.0),
    )
    run("0.1% slippage", lambda b: b.set_slippage_perc(0.001))
    run("cheat-on-close", lambda b: b.set_coc(True))


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
