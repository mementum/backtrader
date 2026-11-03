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
"""Strategies without a strategy class: signals.

A signal is an indicator whose value says what to do: positive means long,
negative short, zero nothing. ``cerebro.add_signal`` attaches it with a
role, and cerebro builds the strategy that trades it:

- ``SIGNAL_LONGSHORT``: long when positive, short when negative
- ``SIGNAL_LONG``: long when positive, flat when negative
- ``SIGNAL_LONGEXIT``: an extra signal that exits a long when negative

Run it:  python examples/12_signals.py [--plot]
"""

import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class PriceAboveSma(bt.Indicator):
    """Positive while the close is above its 30-bar average, negative below:
    the distance between the two, of which only the sign is used."""

    lines = ("signal",)

    def __init__(self):
        self.lines.signal = self.data.close - bt.ind.SMA(period=30)


class RsiOverbought(bt.Indicator):
    """Negative (exit) while RSI is above 70."""

    lines = ("signal",)

    def __init__(self):
        self.lines.signal = 70.0 - bt.ind.RSI(period=14)


def run(label, *signals, plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(
        bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    )
    for kind, indicator in signals:
        cerebro.add_signal(kind, indicator)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    cerebro.broker.setcash(100_000.0)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    strat = cerebro.run()[0]
    trades = strat.analyzers.trades.get_analysis().total.get("closed", 0)
    pnl = cerebro.broker.getvalue() - 100_000.0
    print(f"{label:30s} {trades:3d} trades, profit {pnl:9.2f}")
    if plot:
        cerebro.plot()


def main(plot=False):
    run("long/short above/below SMA", (bt.SIGNAL_LONGSHORT, PriceAboveSma), plot=plot)
    run("long only", (bt.SIGNAL_LONG, PriceAboveSma))
    run(
        "long only, exit when RSI > 70",
        (bt.SIGNAL_LONG, PriceAboveSma),
        (bt.SIGNAL_LONGEXIT, RsiOverbought),
    )


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
