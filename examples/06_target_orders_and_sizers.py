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
"""How much to trade: target orders and sizers.

- ``order_target_percent(target=0.5)`` buys or sells whatever it takes to
  make the position 50% of the portfolio's value. ``order_target_value``
  and ``order_target_size`` do the same in money and in units.
- A sizer decides the size when ``buy()``/``sell()`` are called without
  one. ``FixedSize`` always trades the same amount, ``PercentSizer`` a share
  of the cash; a custom sizer can use anything (here: risk a fixed amount
  per trade, sized by volatility).

Run it:  python examples/06_target_orders_and_sizers.py [--plot]
"""

import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class Rebalance(bt.Strategy):
    """Holds 30%, 60% and 0% of the portfolio in turn, each for 60 bars."""

    TARGETS = (0.3, 0.6, 0.0)

    def next(self):
        if len(self) % 60 == 1:
            target = self.TARGETS[(len(self) // 60) % 3]
            self.order_target_percent(target=target)
            self.target = target

    def notify_order(self, order):
        if order.status == order.Completed:
            weight = self.position.size * self.data.close[0] / self.broker.getvalue()
            print(
                f"{self.data.datetime.date(0)} target {self.target:.0%}: "
                f"{'bought' if order.isbuy() else 'sold'} "
                f"{abs(order.executed.size):.0f}, now {weight:.1%} of the portfolio"
            )


class VolatilityRiskSizer(bt.Sizer):
    """Sizes so that a move of ``atrs`` average true ranges against the
    position loses about ``risk`` in money."""

    params = (("risk", 1000.0), ("atrs", 2.0))

    def _getsizing(self, comminfo, cash, data, isbuy):
        atr = self.strategy.atr[0]
        return int(self.p.risk / (self.p.atrs * atr))


class SizedEntries(bt.Strategy):
    def __init__(self):
        self.atr = bt.ind.ATR(period=14)

    def next(self):
        if len(self) == 20:
            self.buy()  # no size: the sizer decides
        elif len(self) == 40:
            self.close()

    def notify_order(self, order):
        if order.status == order.Completed and order.isbuy():
            print(
                f"  {self.sizer.__class__.__name__}: bought {order.executed.size:.0f}"
            )


def main(plot=False):
    data = DATAS / "2006-day-001.txt"

    print("Target orders:")
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(bt.feeds.BacktraderCSVData(dataname=str(data)))
    cerebro.addstrategy(Rebalance)
    cerebro.broker.setcash(1_000_000.0)
    cerebro.run()
    if plot:
        cerebro.plot()

    print("Sizers, each deciding the size of the same entry:")
    for sizer, kwargs in (
        (bt.sizers.FixedSize, dict(stake=25)),
        (bt.sizers.PercentSizer, dict(percents=20)),
        (VolatilityRiskSizer, dict(risk=1000.0)),
    ):
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(bt.feeds.BacktraderCSVData(dataname=str(data)))
        cerebro.addstrategy(SizedEntries)
        cerebro.addsizer(sizer, **kwargs)
        cerebro.broker.setcash(1_000_000.0)
        cerebro.run()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
