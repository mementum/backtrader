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
"""Selling puts for income: the cash-secured put, run as "the wheel".

Each month the strategy sells one put 5% below the market, keeping the cash
to buy the stock at the strike in reserve (that is what "cash-secured"
means: no borrowing is needed if the put is assigned). Then:

- If the put expires worthless, the premium is kept, and next month
  another put is sold.
- If the put is assigned, the broker delivers 100 units at the strike.
  From then on the strategy sells a covered call 5% above the market each
  month instead.
- When a call is assigned, the units are delivered away, and the wheel
  turns back to puts.

The contracts are priced by ``ModelOptionData`` at the index's realised
volatility. Selling options at model prices is optimistic: real puts
trade at a higher implied volatility than the index realises (that gap is
the premium sellers earn), but also cost a bid/ask spread on every trade.

Run it:  python examples/19_options_cash_secured_put.py [--plot]
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


class Wheel(bt.Strategy):
    def __init__(self):
        self.index = self.getdatabyname("index")
        self.options = [d for d in self.datas if d is not self.index]
        self.premiums = 0.0

    def prenext(self):
        self.next()

    def next(self):
        today = self.index.datetime.date(0)
        holding = self.getposition(self.index).size > 0
        for opt in self.options:
            if len(opt) != 1 or opt.datetime.date(0) != today:
                continue  # only act on a contract's listing day
            c = opt.contract
            if c.isput and not holding:
                reserve = c.strike * c.multiplier
                if self.broker.getcash() >= reserve:  # cash-secured
                    self.sell(data=opt, size=1)
            elif c.iscall and holding:
                self.sell(data=opt, size=1)  # covered by the 100 units held

    def notify_order(self, order):
        if order.status != order.Completed:
            return
        day = order.data.datetime.date(0)
        leg = order.info.get("settlement")
        if order.data is self.index:
            verb = "bought" if order.isbuy() else "delivered away"
            print(f"{day}   {verb} 100 units at {order.executed.price:.2f}")
        elif leg is None:
            premium = order.executed.price * order.data.contract.multiplier
            self.premiums += premium
            print(f"{day} sold {order.data._name}, premium {premium:,.2f}")
        else:
            print(f"{day}   {order.data._name}: {leg}")


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    index = bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    cerebro.adddata(index, name="index")
    for month in range(1, 13):
        expiry = third_friday(2006, month)
        for right, moneyness in (("P", 0.95), ("C", 1.05)):
            contract = OptionContract("index", 1, expiry, right)  # physical
            cerebro.addoption(
                ModelOptionData(
                    dataname=index,
                    contract=contract,
                    listing=datetime.date(2006, month, 1),
                    moneyness=moneyness,
                    strikestep=10,
                    rate=0.03,
                ),
                comminfo=OptionCommInfo(commission=0.65, exercise_fee=1.0),
            )
    cerebro.addstrategy(Wheel)
    cerebro.broker.setcash(500_000.0)
    strat = cerebro.run()[0]
    print(f"premiums collected {strat.premiums:,.2f}")
    print(f"final value {cerebro.broker.getvalue():,.2f} from 500,000.00")
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
