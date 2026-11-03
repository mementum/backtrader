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
"""backtrader.options.pricing against published values and its own identities.

The anchors are worked examples from J. C. Hull, *Options, Futures, and Other
Derivatives*: they were computed independently of this code, which is the
point - a value this module printed itself would bless whatever it does.
"""

import math

import pytest

from backtrader.options import pricing as px


def test_bsm_matches_hulls_call_and_put():
    # S=42, K=40, r=10%, sigma=20%, T=0.5: c = 4.76, p = 0.81
    assert round(px.bsm("C", 42, 40, 0.5, 0.10, 0.20).price, 2) == 4.76
    assert round(px.bsm("P", 42, 40, 0.5, 0.10, 0.20).price, 2) == 0.81


def test_bsm_greeks_match_hulls_worked_example():
    # S=49, K=50, r=5%, sigma=20%, T=20 weeks: the Greek letters chapter
    g = px.bsm("call", 49, 50, 20 / 52, 0.05, 0.20)
    assert round(g.price, 2) == 2.40
    assert round(g.delta, 3) == 0.522
    assert round(g.gamma, 3) == 0.066
    assert round(g.vega, 1) == 12.1
    assert round(g.theta, 2) == -4.31
    assert round(g.rho, 2) == 8.91


def test_black76_matches_hulls_futures_put():
    # F=20, K=20, r=9%, sigma=25%, T=4 months: p = 1.12
    assert round(px.black76("P", 20, 20, 4 / 12, 0.09, 0.25).price, 2) == 1.12


def test_binomial_american_put_matches_hull():
    # S=50, K=50, r=10%, sigma=40%, T=5 months: 5 steps 4.49, 500 steps 4.283
    assert round(px.binomial("P", 50, 50, 5 / 12, 0.10, 0.40, steps=5), 2) == 4.49
    assert round(px.binomial("P", 50, 50, 5 / 12, 0.10, 0.40, steps=500), 3) == 4.283


@pytest.mark.parametrize("q", [0.0, 0.03])
def test_put_call_parity(q):
    S, K, T, r, sig = 100.0, 95.0, 0.75, 0.04, 0.3
    c = px.bsm("C", S, K, T, r, sig, q).price
    p = px.bsm("P", S, K, T, r, sig, q).price
    assert c - p == pytest.approx(S * math.exp(-q * T) - K * math.exp(-r * T))


def test_european_tree_converges_to_bsm():
    tree = px.binomial("C", 100, 105, 1.0, 0.05, 0.25, steps=2000, american=False)
    assert tree == pytest.approx(px.bsm("C", 100, 105, 1.0, 0.05, 0.25).price, abs=2e-3)


def test_american_call_without_dividends_is_european():
    a = px.binomial("C", 100, 100, 1.0, 0.05, 0.3, steps=400)
    e = px.binomial("C", 100, 100, 1.0, 0.05, 0.3, steps=400, american=False)
    assert a == pytest.approx(e)


@pytest.mark.parametrize("name", ["delta", "gamma", "vega", "theta", "rho"])
def test_greeks_agree_with_finite_differences(name):
    S, K, T, r, sig, q, h = 100.0, 110.0, 0.5, 0.03, 0.25, 0.01, 1e-4
    g = px.bsm("P", S, K, T, r, sig, q)

    def price(**kw):
        a = dict(S=S, K=K, T=T, r=r, sigma=sig, q=q) | kw
        return px.bsm("P", **a).price

    numeric = {
        "delta": (price(S=S + h) - price(S=S - h)) / (2 * h),
        # a second difference needs a wider step, or rounding swamps it
        "gamma": (price(S=S + 0.01) - 2 * g.price + price(S=S - 0.01)) / 0.01**2,
        "vega": (price(sigma=sig + h) - price(sigma=sig - h)) / (2 * h),
        "theta": -(price(T=T + h) - price(T=T - h)) / (2 * h),
        "rho": (price(r=r + h) - price(r=r - h)) / (2 * h),
    }[name]
    assert getattr(g, name) == pytest.approx(numeric, rel=1e-4, abs=1e-6)


@pytest.mark.parametrize("right,K", [("C", 90.0), ("C", 120.0), ("P", 100.0)])
def test_implied_vol_recovers_the_volatility_that_priced_the_option(right, K):
    price = px.bsm(right, 100.0, K, 0.4, 0.02, 0.37).price
    assert px.implied_vol(price, right, 100.0, K, 0.4, 0.02) == pytest.approx(0.37)


def test_implied_vol_on_a_tree_recovers_the_volatility():
    price = px.binomial("P", 50, 55, 0.5, 0.05, 0.3, steps=150)
    iv = px.implied_vol(price, "P", 50, 55, 0.5, 0.05, model="binomial", steps=150)
    assert iv == pytest.approx(0.3, abs=1e-6)


def test_implied_vol_is_nan_for_a_price_no_volatility_produces():
    # below intrinsic value (10) for a deep call: no volatility gives that
    assert math.isnan(px.implied_vol(9.0, "C", 110.0, 100.0, 0.5, 0.0))


@pytest.mark.parametrize("model", ["bsm", "black76", "binomial"])
@pytest.mark.parametrize("price", [0.0, 1e-13])
def test_implied_vol_is_nan_for_a_worthless_option(model, price):
    """A price every low volatility reproduces to within the tolerance
    identifies no volatility. The solver returned its first guess, 0.2."""
    iv = px.implied_vol(price, "C", 100.0, 150.0, 2 / 365, 0.03, model=model)
    assert math.isnan(iv)


def test_implied_vol_still_finds_a_small_but_real_price():
    price = px.bsm("C", 100.0, 130.0, 20 / 365, 0.03, 0.4).price
    assert 1e-4 < price < 1e-2
    assert px.implied_vol(price, "C", 100.0, 130.0, 20 / 365, 0.03) == pytest.approx(
        0.4, rel=1e-6
    )


def test_expiry_and_zero_volatility_are_intrinsic_or_forward():
    assert px.bsm("C", 105, 100, 0.0, 0.05, 0.2).price == 5.0
    assert px.bsm("P", 105, 100, 0.0, 0.05, 0.2).price == 0.0
    fwd = 105 - 100 * math.exp(-0.05)
    assert px.bsm("C", 105, 100, 1.0, 0.05, 0.0).price == pytest.approx(fwd)


@pytest.mark.parametrize("bad", ["X", "", "straddle"])
def test_an_unknown_right_is_refused(bad):
    with pytest.raises(ValueError):
        px.normalize_right(bad)


def test_a_price_far_out_of_the_money_is_never_below_zero():
    # rounding in K e^-rT N(-d2) - S N(-d1) used to give -0.0 here, printed
    # as a negative premium
    price = px.bsm("P", 3832.43, 3510, 1 / 365, 0.03, 0.2).price
    assert math.copysign(1.0, price) == 1.0
