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
"""Stock and options together: a zero-cost protective collar.

A collar protects an equity position against severe downturns while capping
upside potential:

- Holds 100 shares of underlying equity.
- Each month, the strategy buys an out-of-the-money protective Put (5% below
  market) to establish a firm floor on losses.
- Simultaneously, it sells an out-of-the-money Call (5% above market) against
  the shares to generate premium that finances the protective put.

If the stock plunges, the put limits the drawdown; if the stock rallies,
gains are capped at the call strike; if the stock stays between strikes,
both options expire and a new monthly collar is established.

Run it:  python examples/23_options_collar.py [--plot]
"""

import collections
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


class ProtectiveCollar(bt.Strategy):
    def __init__(self):
        self.stock = self.getdatabyname("stock")
        self.months = collections.defaultdict(dict)
        for d in self.datas:
            if d is not self.stock:
                self.months[d.contract.expiry][(d.contract.right, d.p.moneyness)] = d
        self.put_cost = 0.0
        self.call_premium = 0.0
        self.put_payout = 0.0

    def prenext(self):
        self.next()

    def next(self):
        today = self.stock.datetime.date(0)
        # Ensure we hold the underlying stock
        if not self.getposition(self.stock):
            self.buy(data=self.stock, size=100)

        # Enter the monthly collar on contract listing date
        for expiry, legs in self.months.items():
            call = legs.get(("C", 1.05))
            put = legs.get(("P", 0.95))
            if call and put and len(call) == 1 and call.datetime.date(0) == today:
                # Sell covered call, buy protective put
                self.sell(data=call, size=1)
                self.buy(data=put, size=1)

    def notify_order(self, order):
        if order.status != order.Completed:
            return
        day = order.data.datetime.date(0)
        c = getattr(order.data, "contract", None)
        if order.data is self.stock:
            verb = "bought" if order.isbuy() else "sold"
            print(f"{day}   {verb} 100 shares at {order.executed.price:.2f}")
        elif c is not None:
            leg = order.info.get("settlement")
            value = abs(order.executed.price) * c.multiplier
            if leg:
                if c.isput:
                    self.put_payout += value
                print(f"{day}   {order.data._name}: {leg}, value {value:,.2f}")
            elif c.iscall:
                self.call_premium += value
                print(f"{day} sold call {order.data._name}, premium {value:,.2f}")
            elif c.isput:
                self.put_cost += value
                print(f"{day} bought put {order.data._name}, cost {value:,.2f}")


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    stock = bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    cerebro.adddata(stock, name="stock")

    for month in range(1, 13):
        expiry = third_friday(2006, month)
        for right, moneyness in (("C", 1.05), ("P", 0.95)):
            contract = OptionContract("stock", 1, expiry, right, settlement="cash")
            cerebro.addoption(
                ModelOptionData(
                    dataname=stock,
                    contract=contract,
                    listing=datetime.date(2006, month, 1),
                    moneyness=moneyness,
                    strikestep=10,
                    rate=0.03,
                ),
                comminfo=OptionCommInfo(commission=0.65),
            )

    cerebro.addstrategy(ProtectiveCollar)
    cerebro.broker.setcash(500_000.0)
    strat = cerebro.run()[0]

    net_option_cost = strat.put_cost - strat.call_premium - strat.put_payout
    print(
        f"calls sold: {strat.call_premium:,.2f}, puts bought: {strat.put_cost:,.2f}, "
        f"put payouts: {strat.put_payout:,.2f} (net option drag: {net_option_cost:+,.2f})"
    )
    print(f"final portfolio value: {cerebro.broker.getvalue():,.2f} from 500,000.00")

    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
