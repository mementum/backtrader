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
"""Searching parameters: optimisation.

``optstrategy`` runs the strategy once for every combination of the
parameter values given (here 4 x 3 = 12 runs), in parallel when
``maxcpus`` allows. Each run returns its strategy, with its analyzers,
so the combinations can be ranked afterwards.

A caution that applies to every optimiser: the best combination on past
data is partly the best fit to that data's noise. Check it on data it was
not chosen on.

Run it:  python examples/10_optimization.py [--cpus N] [--plot]
"""

import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class SmaCross(bt.Strategy):
    params = (("fast", 10), ("slow", 30))

    def __init__(self):
        self.cross = bt.ind.CrossOver(
            bt.ind.SMA(period=self.p.fast), bt.ind.SMA(period=self.p.slow)
        )

    def next(self):
        if self.cross[0] > 0:
            self.order_target_percent(target=0.95)
        elif self.cross[0] < 0:
            self.order_target_percent(target=0.0)


def main(plot=False, cpus=1):
    cerebro = bt.Cerebro(maxcpus=cpus, stdstats=False)
    cerebro.adddata(
        bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2005-2006-day-001.txt"))
    )
    cerebro.optstrategy(SmaCross, fast=[5, 10, 15, 20], slow=[30, 50, 80])
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.broker.setcash(100_000.0)

    results = []
    for (strat,) in cerebro.run():
        ret = strat.analyzers.returns.get_analysis()["rtot"]
        dd = strat.analyzers.drawdown.get_analysis().max.drawdown / 100
        results.append((ret, dd, strat.p.fast, strat.p.slow))

    print(" fast  slow   return  max drawdown")
    for ret, dd, fast, slow in sorted(results, reverse=True):
        print(f"{fast:5d} {slow:5d} {ret:8.2%} {dd:12.2%}")

    if plot and results:
        best_ret, best_dd, best_fast, best_slow = sorted(results, reverse=True)[0]
        cerebro_plot = bt.Cerebro(stdstats=False)
        cerebro_plot.adddata(
            bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2005-2006-day-001.txt"))
        )
        cerebro_plot.addstrategy(SmaCross, fast=best_fast, slow=best_slow)
        cerebro_plot.broker.setcash(100_000.0)
        cerebro_plot.run()
        cerebro_plot.plot()

    return results


if __name__ == "__main__":
    cpus = int(sys.argv[sys.argv.index("--cpus") + 1]) if "--cpus" in sys.argv else 1
    main(plot="--plot" in sys.argv, cpus=cpus)
