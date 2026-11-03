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
"""Options that roll: a monthly protective put, priced by a model.

Real strategies trade a new contract every month. Each contract is its own
data feed, listed on its first day and gone after expiry. This example has
no option market data, so ``ModelOptionData`` prices each contract from the
index itself. Every month it lists a put 5% below the previous close,
expiring on the third Friday, priced by Black-Scholes at the index's
realised volatility, and the strategy buys it on its first day.

Three things to notice:

- A feed that has not started yet holds the strategy in ``prenext``. This
  strategy simply runs ``next`` there too.
- A contract still held at expiry is settled by the broker, in cash here:
  the put pays its intrinsic value if the index closed below the strike.
- Model prices are not market prices. Real puts carry a skew (out-of-the-
  money puts trade at higher implied volatility) and a bid/ask spread, so
  protection costs more than this shows. That is why the feeds' names end
  in "(model)".

Run it:  python examples/17_options_rolling_puts.py [--plot]
"""

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


class ProtectivePut(bt.Strategy):
    def __init__(self):
        self.index = self.getdatabyname("index")
        self.puts = [d for d in self.datas if d is not self.index]
        self.bought = set()
        self.cost = self.payout = 0.0

    def prenext(self):
        self.next()  # later contracts have no bars yet; trade anyway

    def next(self):
        if not self.getposition(self.index):
            self.buy(data=self.index, size=100)
        for put in self.puts:
            listed_today = put.datetime.date(0) == self.index.datetime.date(0)
            if len(put) == 1 and listed_today and put not in self.bought:
                self.buy(data=put, size=1)
                self.bought.add(put)

    def notify_order(self, order):
        if order.status != order.Completed or order.data is self.index:
            return
        value = abs(order.executed.price) * order.data.contract.multiplier
        if order.info.get("settlement"):
            self.payout += value
            print(
                f"{order.data.datetime.date(0)} {order.data._name} "
                f"(strike {order.data.contract.strike:g}): "
                f"{order.info.settlement}, pays {value:8.2f}"
            )
        else:
            self.cost += value


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    index = bt.feeds.BacktraderCSVData(dataname=str(DATAS / "2006-day-001.txt"))
    cerebro.adddata(index, name="index")  # the underlying goes in first
    for month in range(1, 13):
        expiry = third_friday(2006, month)
        contract = OptionContract("index", 1, expiry, "P", settlement="cash")
        put = ModelOptionData(
            dataname=index,
            contract=contract,  # strike 1 is a placeholder: moneyness sets it
            listing=datetime.date(2006, month, 1),
            moneyness=0.95,
            strikestep=10,
            rate=0.03,
        )
        cerebro.addoption(put)
    cerebro.addstrategy(ProtectivePut)
    cerebro.broker.setcash(1_000_000.0)
    strat = cerebro.run()[0]

    print(f"puts bought for {strat.cost:,.2f}, paid out {strat.payout:,.2f}")
    print(f"final value {cerebro.broker.getvalue():,.2f} from 1,000,000.00")
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
