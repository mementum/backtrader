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
"""Whole option chains: picking contracts by delta across several stocks.

Earlier examples add one data feed per option contract. That does not scale
to full chains: thousands of contracts per stock, listed and expiring every
month. An ``OptionChain`` holds each stock's whole chain for the day
instead, and hands out a ``ContractView`` only for the contracts a strategy
picks. The broker, margin, settlement and analyzers treat a view like any
data feed.

Each month this strategy sells, on each of three stocks, the put closest to
a delta of -0.30 among those 20 to 50 days from expiry. That is a common
way of selling puts: by risk, not by a fixed distance from the price.
``chain.select`` finds it, implying each strike's volatility from its
price. The puts are cash-secured (``CashCovered``) and fill halfway into
the spread (``set_quotefill``).

The chains are model-priced (``ModelChainSource``), since the repository
holds no option chain data. With real data, ``PandasChainSource`` takes a
DataFrame of daily chains, and ``PartitionedChainSource`` loads it a year or
a month at a time, so that ten years of chains need not fit in memory.

Run it:  python examples/22_options_chains.py [--plot]
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


class SellPutsByDelta(bt.Strategy):
    def __init__(self):
        self.month = None

    def next(self):
        day = self.data0.datetime.date(0)
        if day.month == self.month:
            return
        self.month = day.month
        for d in self.datas:
            chain = self.getchain(d._name)
            put = chain.select("P", dte=(20, 50), delta=-0.30)
            if put is not None:
                self.combo([(put, -10)])  # 10 contracts, as one structure

    def notify_order(self, order):
        if order.status == order.Margin:
            print(f"{self.data0.datetime.date(0)} not secured: {order.data._name}")


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
    cerebro.addanalyzer(StructureTrades, _name="puts")
    cerebro.addstrategy(SellPutsByDelta)
    strat = cerebro.run()[0]

    results = strat.analyzers.puts.get_analysis()
    assigned = [r for r in results.values() if len(r["legs"]) > 1]
    won = sum(r["pnl"] > 0 for r in results.values())
    print(f"{len(results)} puts sold, {won} profitable, {len(assigned)} assigned")
    for r in sorted(results.values(), key=lambda r: r["pnl"])[:3]:
        print(f"  worst: {r['legs'][0]:28s} {r['pnl']:+10,.2f}")
    for d in strat.datas:
        held = strat.getposition(d).size
        if held:
            print(f"holding {held:.0f} {d._name} from assignment")
    print(f"final value {cerebro.broker.getvalue():,.2f} from 250,000.00")
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
