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
"""Stock and options together: a covered strangle for enhanced yield.

A covered strangle combines a long equity position with selling both an
out-of-the-money Call and an out-of-the-money Put:

- Holds shares in the underlying stock.
- Sells an out-of-the-money Call (105% moneyness) covered by the shares held.
- Simultaneously sells an out-of-the-money Put (95% moneyness) backed by cash
  reserve.

This collects premium from both wings simultaneously:

- In neutral/range-bound markets, both options expire worthless and the
  strategy keeps all premiums.
- On a strong rally past the call strike, stock is called away at the strike,
  realizing capital gains plus collected premiums.
- On a sharp drop below the put strike, the put is assigned and delivers
  shares at the strike price, buying the dip at an effective discount.

Run it:  python examples/24_options_covered_strangle.py [--plot]
"""

import datetime
import sys
from pathlib import Path

import backtrader as bt
from backtrader.options import ModelOptionData, OptionCommInfo, OptionContract

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


def third_friday(year, month):
    day = datetime.date(year, month, 15)
    return day + datetime.timedelta(days=(4 - day.weekday()) % 7)


class CoveredStrangle(bt.Strategy):
    def __init__(self):
        self.stock = self.getdatabyname("stock")
        self.options = [d for d in self.datas if d is not self.stock]
        self.total_premiums = 0.0

    def prenext(self):
        self.next()

    def next(self):
        today = self.stock.datetime.date(0)
        pos = self.getposition(self.stock).size

        # Initial long equity position if flat
        if pos <= 0 and len(self) == 1:
            self.buy(data=self.stock, size=100)

        for opt in self.options:
            if len(opt) != 1 or opt.datetime.date(0) != today:
                continue
            c = opt.contract
            # Sell 1 covered call if holding stock (up to number of 100-share blocks)
            if c.iscall and pos >= 100:
                self.sell(data=opt, size=1)
            # Sell 1 cash-secured put if sufficient cash is available
            elif c.isput:
                reserve = c.strike * c.multiplier
                if self.broker.getcash() >= reserve:
                    self.sell(data=opt, size=1)

    def notify_order(self, order):
        if order.status != order.Completed:
            return
        day = order.data.datetime.date(0)
        leg = order.info.get("settlement")

        if order.data is self.stock:
            action = "bought" if order.isbuy() else "delivered away"
            print(
                f"{day} [Stock] {action} {abs(order.executed.size):.0f} shares at {order.executed.price:.2f}"
            )
        elif leg is None:
            premium = order.executed.price * order.data.contract.multiplier
            self.total_premiums += premium
            print(
                f"{day} [Option] sold {order.data._name}, collected premium {premium:,.2f}"
            )
        else:
            print(f"{day} [Option] {order.data._name}: {leg}")


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    stock = bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    cerebro.adddata(stock, name="stock")

    for month in range(1, 13):
        expiry = third_friday(2006, month)
        for right, moneyness in (("C", 1.05), ("P", 0.95)):
            contract = OptionContract("stock", 1, expiry, right, settlement="physical")
            cerebro.addoption(
                ModelOptionData(
                    dataname=stock,
                    contract=contract,
                    listing=datetime.date(2006, month, 1),
                    moneyness=moneyness,
                    strikestep=10,
                    rate=0.03,
                ),
                comminfo=OptionCommInfo(commission=0.65, exercise_fee=1.0),
            )

    cerebro.addstrategy(CoveredStrangle)
    cerebro.broker.setcash(1_000_000.0)
    strat = cerebro.run()[0]

    final_shares = strat.getposition(strat.stock).size
    print(f"total option premiums collected: {strat.total_premiums:,.2f}")
    print(f"ending stock position: {final_shares:.0f} shares")
    print(f"final portfolio value: {cerebro.broker.getvalue():,.2f} from 1,000,000.00")

    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
