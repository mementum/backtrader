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
"""Multi-stock portfolio with dynamic option chains: delta-selected collars.

Managing options alongside stock positions across multiple equities:

- Holds a basket of equities (NVDA, ORCL, YHOO).
- Each month, the strategy queries each stock's dynamic ``OptionChain``.
- Instead of fixed strikes, it selects option legs by their Greeks:
  - Buys a protective Put with delta ≈ -0.25 (20 to 50 DTE) for downside tail
    protection.
  - Sells a covered Call with delta ≈ +0.25 (20 to 50 DTE) to finance the hedge.
- Executes the combined legs as a unified structure trade using ``self.combo``.
- Combines stock feeds, option chains (``OptionChain``, ``ModelChainSource``),
  the ``CashCovered`` margin model, and ``StructureTrades`` analyzer.

Run it:  python examples/25_options_stock_collar_chains.py [--plot]
"""

import sys
from pathlib import Path

import backtrader as bt
from backtrader.options import (
    CashCovered,
    ModelChainSource,
    OptionChain,
    OptionCommInfo,
    StructureTrades,
)

REQUIRES = ("numpy",)
DATAS = Path(__file__).resolve().parent.parent / "datas"
STOCKS = ("nvda", "orcl", "yhoo")


class MultiStockCollarChain(bt.Strategy):
    def __init__(self):
        self.month = None

    def next(self):
        day = self.data0.datetime.date(0)

        # Rebalance monthly across all stocks in the portfolio
        if day.month != self.month:
            self.month = day.month
            for d in self.datas:
                if self.getposition(d).size < 100:
                    self.buy(data=d, size=100)
                    continue

                chain = self.getchain(d._name)
                put = chain.select("P", dte=(20, 50), delta=-0.25)
                call = chain.select("C", dte=(20, 50), delta=0.25)

                if put is not None and call is not None:
                    # 1 covered call sold (-1), 1 protective put bought (+1)
                    self.combo([(call, -1), (put, 1)])

    def notify_order(self, order):
        if order.status == order.Margin:
            pass  # active collar on stock already covers position under CashCovered
        elif order.status == order.Completed:
            leg = order.info.get("settlement")
            if leg == "delivery":
                print(
                    f"{order.data.datetime.date(0)} physical delivery: {order.data._name} {order.executed.size:+.0f} shares at {order.executed.price:.2f}"
                )


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)

    for name in STOCKS:
        data = bt.feeds.YahooFinanceCSVData(dataname=str(DATAS / f"{name}-2014.txt"))
        cerebro.adddata(data, name=name)
        source = ModelChainSource(strikestep=0.5, width=0.25, rate=0.01, spread=0.05)
        chain = OptionChain(data, source, settlement="physical", rate=0.01)
        cerebro.addchain(chain, comminfo=OptionCommInfo(commission=0.65))

    cerebro.broker.setcash(250_000.0)
    cerebro.broker.set_margin_model(CashCovered())
    cerebro.broker.set_quotefill(0.5)
    cerebro.addanalyzer(StructureTrades, _name="collars")
    cerebro.addstrategy(MultiStockCollarChain)

    strat = cerebro.run()[0]
    results = strat.analyzers.collars.get_analysis()

    print(f"Executed {len(results)} collar combo structures across portfolio:")
    for key, r in list(results.items())[:6]:
        legs_str = ", ".join(r["legs"])
        print(f"  {r['opened']} -> {r['closed']}: PnL {r['pnl']:+8.2f} [{legs_str}]")

    print("\nStock positions:")
    for d in strat.datas:
        pos = strat.getposition(d).size
        print(f"  {d._name}: {pos:.0f} shares")

    print(f"Final portfolio value: {cerebro.broker.getvalue():,.2f} from 250,000.00")

    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
