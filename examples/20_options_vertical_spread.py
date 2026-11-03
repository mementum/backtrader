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
"""A defined-risk structure: the monthly bull call spread.

Each month the strategy buys a call at the money and sells a call 5% higher,
both expiring on the third Friday. The pair costs less than the call alone
(the sold call pays part of it), and its outcome is bounded at expiry:

- below the lower strike, both expire worthless: the loss is the net debit;
- above the upper strike, the spread pays the gap between the strikes: the
  gain is that gap minus the debit;
- in between, it pays what the index is above the lower strike.

Both legs are separate orders on separate feeds. The broker checks each one
against cash on its own, and in the order sent. With too little cash, a
long leg sent first can be refused while the short leg still fills,
leaving a naked short call. So this sends the short leg first, whose
premium helps pay for the long one. ``self.combo`` sends the legs as one
order instead, checked and filled together: see example 21.

Run it:  python examples/20_options_vertical_spread.py [--plot]
"""

import collections
import datetime
import sys
from pathlib import Path

import backtrader as bt
from backtrader.options import ModelOptionData, OptionContract

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


def third_friday(year, month):
    day = datetime.date(year, month, 15)
    return day + datetime.timedelta(days=(4 - day.weekday()) % 7)


class BullCallSpread(bt.Strategy):
    def __init__(self):
        self.index = self.getdatabyname("index")
        months = collections.defaultdict(dict)
        for d in self.datas:
            if d is not self.index:
                months[d.contract.expiry][d.p.moneyness] = d
        self.months = months  # expiry -> {1.00: long leg, 1.05: short leg}
        self.cash_flow = collections.defaultdict(float)

    def prenext(self):
        self.next()

    def next(self):
        today = self.index.datetime.date(0)
        for expiry, legs in self.months.items():
            low, high = legs[1.00], legs[1.05]
            if len(low) == 1 and low.datetime.date(0) == today:
                self.sell(data=high, size=1)  # short leg first: its premium
                self.buy(data=low, size=1)  # helps pay for the long leg

    def notify_order(self, order):
        if order.status == order.Completed:
            c = order.data.contract
            # cash in (sold) or out (bought), per contract
            self.cash_flow[c.expiry] -= (
                order.executed.size * order.executed.price * c.multiplier
            )

    def stop(self):
        for expiry, legs in sorted(self.months.items()):
            low, high = legs[1.00].contract, legs[1.05].contract
            width = (high.strike - low.strike) * low.multiplier
            print(
                f"{expiry} {low.strike:g}/{high.strike:g}: "
                f"result {self.cash_flow[expiry]:+10,.2f}  (max gain {width:,.0f} - debit)"
            )


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    index = bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    cerebro.adddata(index, name="index")
    for month in range(1, 13):
        expiry = third_friday(2006, month)
        for moneyness in (1.00, 1.05):
            contract = OptionContract("index", 1, expiry, "C", settlement="cash")
            cerebro.addoption(
                ModelOptionData(
                    dataname=index,
                    contract=contract,
                    listing=datetime.date(2006, month, 1),
                    moneyness=moneyness,
                    strikestep=10,
                    rate=0.03,
                )
            )
    cerebro.addstrategy(BullCallSpread)
    cerebro.broker.setcash(100_000.0)
    cerebro.run()
    print(f"final value {cerebro.broker.getvalue():,.2f} from 100,000.00")
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
