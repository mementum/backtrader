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
"""Broker simulation: cash and value accounting, the order types, commission
schemes and slippage.

backtrader/brokers/bbroker.py is the single largest piece of behaviour in the
package and had no test of its own.
"""

import pytest

import backtrader as bt

from conftest import csvdata


class OrderRecorder(bt.Strategy):
    """Places one order on a given bar and records every notification."""

    __test__ = False

    params = dict(
        when=5,  # bar index (1-based, as len(self)) to act on
        size=10,
        action="buy",
        exectype=None,
        price=None,
        valid=None,
    )

    def __init__(self):
        self.orders = []
        self.notifications = []
        self.cash_at_order = None
        self.trades = []

    def notify_order(self, order):
        self.notifications.append((order.status, order.getstatusname()))

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append(trade)

    def next(self):
        if len(self) != self.p.when:
            return
        self.cash_at_order = self.broker.getcash()
        kwargs = dict(size=self.p.size)
        if self.p.exectype is not None:
            kwargs["exectype"] = self.p.exectype
        if self.p.price is not None:
            kwargs["price"] = self.p.price
        if self.p.valid is not None:
            kwargs["valid"] = self.p.valid
        fn = self.buy if self.p.action == "buy" else self.sell
        self.orders.append(fn(**kwargs))


def run(strategy=OrderRecorder, cash=100000.0, data=None, **kwargs):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(cash)
    cerebro.adddata(data if data is not None else csvdata())
    cerebro.addstrategy(strategy, **kwargs)
    return cerebro.run()[0], cerebro


class TestCashAndValue:
    def test_initial_cash_is_what_was_set(self):
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(12345.0)
        assert cerebro.broker.getcash() == 12345.0
        assert cerebro.broker.getvalue() == 12345.0

    def test_value_equals_cash_with_no_position(self):
        strat, cerebro = run(size=0)
        assert cerebro.broker.getvalue() == pytest.approx(cerebro.broker.getcash())

    def test_buying_moves_cash_into_position_value(self):
        strat, cerebro = run()
        pos = strat.getposition(strat.data)
        assert pos.size == 10
        # cash went down by roughly the cost of the position
        assert cerebro.broker.getcash() < strat.cash_at_order
        # and total value is still cash + what the position is worth
        expected = cerebro.broker.getcash() + pos.size * strat.data.close[0]
        assert cerebro.broker.getvalue() == pytest.approx(expected)

    def test_set_cash_and_add_cash_agree(self):
        broker = bt.brokers.BackBroker()
        broker.setcash(1000.0)
        broker.add_cash(500.0)
        broker.init()
        assert broker.startingcash == 1000.0


class TestOrderTypes:
    def test_market_order_executes_on_the_next_open(self):
        strat, _ = run(exectype=bt.Order.Market)
        order = strat.orders[0]
        assert order.status == bt.Order.Completed
        assert order.executed.size == 10
        assert order.executed.price > 0

    def test_limit_order_far_from_price_never_fills(self):
        strat, _ = run(exectype=bt.Order.Limit, price=1.0, size=10)
        order = strat.orders[0]
        assert order.status != bt.Order.Completed
        assert strat.getposition(strat.data).size == 0

    def test_limit_order_above_market_fills(self):
        # a buy limit above the market is marketable; keep it affordable,
        # because the margin check reserves cash at the *limit* price
        strat, _ = run(exectype=bt.Order.Limit, price=10000.0, size=1)
        assert strat.orders[0].status == bt.Order.Completed
        assert strat.getposition(strat.data).size == 1

    def test_sell_order_opens_a_short(self):
        strat, _ = run(action="sell", size=7)
        assert strat.getposition(strat.data).size == -7

    def test_close_flattens_the_position(self):
        class BuyThenClose(bt.Strategy):
            __test__ = False

            def next(self):
                if len(self) == 5:
                    self.buy(size=10)
                elif len(self) == 10:
                    self.close()

        strat, _ = run(strategy=BuyThenClose)
        assert strat.getposition(strat.data).size == 0

    def test_cancel_removes_a_pending_order(self):
        class CancelIt(bt.Strategy):
            __test__ = False

            def __init__(self):
                self.order = None
                self.cancelled = False

            def next(self):
                if len(self) == 5:
                    self.order = self.buy(exectype=bt.Order.Limit, price=1.0)
                elif len(self) == 6:
                    self.cancel(self.order)
                    self.cancelled = True

        strat, _ = run(strategy=CancelIt)
        assert strat.cancelled
        assert strat.order.status == bt.Order.Canceled

    @pytest.mark.parametrize("exectype", [bt.Order.Market, bt.Order.Limit])
    def test_cancel_on_the_bar_that_created_the_order(self, exectype):
        """A new order waits in the broker's submitted queue until its next
        cycle. cancel() looked only among the pending orders, returned False,
        and the order went on to be accepted - and a market order filled."""

        class CancelAtOnce(bt.Strategy):
            __test__ = False

            def __init__(self):
                self.statuses = []

            def next(self):
                if len(self) == 5:
                    price = self.data.close[0] * 0.5
                    self.order = self.buy(size=10, exectype=exectype, price=price)
                    self.result = self.cancel(self.order)

            def notify_order(self, order):
                self.statuses.append(order.getstatusname())

        strat, _ = run(strategy=CancelAtOnce)
        assert strat.order.status == bt.Order.Canceled
        assert strat.statuses == ["Submitted", "Canceled"]
        assert strat.getposition(strat.data).size == 0

    def test_cancelling_one_new_combo_leg_cancels_the_combo(self):
        class ComboThenCancel(bt.Strategy):
            __test__ = False

            def next(self):
                if len(self) == 5:
                    self.legs = self.combo([(self.data0, 10), (self.data1, -10)])
                    self.cancel(self.legs[0])

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(csvdata())
        cerebro.adddata(csvdata())
        cerebro.broker.setcash(100000.0)
        cerebro.addstrategy(ComboThenCancel)
        strat = cerebro.run()[0]
        assert [leg.status for leg in strat.legs] == [bt.Order.Canceled] * 2
        assert strat.getposition(strat.data0).size == 0
        assert strat.getposition(strat.data1).size == 0

    def test_order_rejected_when_cash_is_insufficient(self):
        strat, _ = run(cash=10.0, size=1000)
        assert strat.orders[0].status in (bt.Order.Margin, bt.Order.Rejected)
        assert strat.getposition(strat.data).size == 0


class TestCommission:
    def test_percentage_commission_reduces_cash(self):
        def value_with(commission):
            cerebro = bt.Cerebro(stdstats=False)
            cerebro.broker.setcash(100000.0)
            cerebro.broker.setcommission(commission=commission)
            cerebro.adddata(csvdata())
            cerebro.addstrategy(OrderRecorder)
            cerebro.run()
            return cerebro.broker.getvalue()

        assert value_with(0.01) < value_with(0.0)

    def test_commission_is_charged_on_both_legs(self):
        class RoundTrip(bt.Strategy):
            __test__ = False

            def next(self):
                if len(self) == 5:
                    self.buy(size=10)
                elif len(self) == 10:
                    self.sell(size=10)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(
            commission=2.0, commtype=bt.CommInfoBase.COMM_FIXED
        )
        cerebro.adddata(csvdata())
        cerebro.addstrategy(RoundTrip)
        cerebro.run()
        # 10 units * 2.0 per unit, twice
        charged = 100000.0 - cerebro.broker.getvalue()
        assert charged >= 40.0

    def test_getcommissioninfo_returns_the_configured_scheme(self):
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcommission(commission=0.005)
        data = csvdata()
        cerebro.adddata(data)
        cerebro.addstrategy(OrderRecorder)
        cerebro.run()
        comminfo = cerebro.broker.getcommissioninfo(data)
        assert comminfo.p.commission == 0.005


class TestSlippage:
    def test_slippage_perc_worsens_the_buy_price(self):
        def buy_price(slip):
            cerebro = bt.Cerebro(stdstats=False)
            cerebro.broker.setcash(100000.0)
            if slip:
                cerebro.broker.set_slippage_perc(slip)
            cerebro.adddata(csvdata())
            cerebro.addstrategy(OrderRecorder)
            strat = cerebro.run()[0]
            return strat.orders[0].executed.price

        assert buy_price(0.01) > buy_price(0.0)

    def test_slippage_fixed_shifts_by_the_given_amount(self):
        def buy_price(slip):
            cerebro = bt.Cerebro(stdstats=False)
            cerebro.broker.setcash(100000.0)
            if slip:
                cerebro.broker.set_slippage_fixed(slip)
            cerebro.adddata(csvdata())
            cerebro.addstrategy(OrderRecorder)
            strat = cerebro.run()[0]
            return strat.orders[0].executed.price

        assert buy_price(5.0) == pytest.approx(buy_price(0.0) + 5.0)


class TestCheatOnOpen:
    def test_coo_fills_at_the_same_bar_open(self):
        cerebro = bt.Cerebro(stdstats=False, cheat_on_open=True)
        cerebro.broker.setcash(100000.0)
        cerebro.adddata(csvdata())

        class COOStrategy(bt.Strategy):
            __test__ = False

            def __init__(self):
                self.order = None
                self.open_at_order = None

            def next_open(self):
                if len(self) == 5 and self.order is None:
                    self.open_at_order = self.data.open[0]
                    self.order = self.buy(size=1)

        cerebro.addstrategy(COOStrategy)
        strat = cerebro.run()[0]
        assert strat.order.executed.price == pytest.approx(strat.open_at_order)
