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
"""Order types, and the life of an order.

Each order type is sent once, on the same bar, and ``notify_order`` reports
what happens to it:

- ``Market``: fills at the next bar's open.
- ``Close``: fills at the next bar's close.
- ``Limit``: a buy fills at the limit price or better, if the market gets
  there.
- ``Stop``: becomes a market order once the price trades through the stop.
- ``StopLimit``: becomes a limit order once the stop is touched.
- ``StopTrail``: a stop that follows the price at a fixed distance.
- ``valid``: a limit that is not filled by then expires.

An order goes Submitted -> Accepted -> Completed, or ends Canceled, Expired,
Margin (not enough cash) or Rejected.

Run it:  python examples/04_order_types.py [--plot]
"""

import datetime
import sys
from pathlib import Path

import backtrader as bt

REQUIRES = ()
DATAS = Path(__file__).resolve().parent.parent / "datas"


class Orders(bt.Strategy):
    def next(self):
        if len(self) != 1:
            return
        close = self.data.close[0]
        print(f"{self.data.datetime.date(0)} close {close:.2f}: sending orders")
        self.buy(size=1, info="market")
        self.buy(size=1, exectype=bt.Order.Close, info="close")
        self.buy(size=1, exectype=bt.Order.Limit, price=close * 0.99, info="limit -1%")
        self.buy(
            size=1,
            exectype=bt.Order.Limit,
            price=close * 0.90,
            valid=datetime.timedelta(days=5),
            info="limit -10%, 5 days",
        )
        self.buy(size=1, exectype=bt.Order.Stop, price=close * 1.02, info="stop +2%")
        self.buy(
            size=1,
            exectype=bt.Order.StopLimit,
            price=close * 1.02,
            plimit=close * 1.025,
            info="stop-limit",
        )
        # a sell stop 3% under the price, raised as the price rises
        self.sell(
            size=1, exectype=bt.Order.StopTrail, trailpercent=0.03, info="trail 3%"
        )

    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            return  # the normal path to execution; nothing to report
        when = self.data.datetime.date(0)
        what = order.info.info
        if order.status == order.Completed:
            side = "bought" if order.isbuy() else "sold"
            print(f"{when} {what:20s} {side} at {order.executed.price:.2f}")
        else:
            print(f"{when} {what:20s} {order.getstatusname()}")


def main(plot=False):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(
        bt.feeds.BacktraderCSVData(
            dataname=str(DATAS / "2006-day-001.txt"),
            todate=datetime.datetime(2006, 3, 31),
        )
    )
    cerebro.addstrategy(Orders)
    cerebro.broker.setcash(100_000.0)  # enough for all seven at once
    cerebro.run()
    if plot:
        cerebro.plot()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
