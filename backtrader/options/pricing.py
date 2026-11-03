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
"""Option prices, greeks and implied volatility, from the standard library only.

Every function takes the option's ``right`` ("C"/"call" or "P"/"put"), the
underlying price ``S`` (the futures price ``F`` for Black-76), the strike
``K``, the time to expiry ``T`` in years, the continuously compounded rate
``r`` and the volatility ``sigma``, both as fractions (0.05, 0.20).

Greeks come in the textbook units: ``vega`` and ``rho`` per 1.0 change
(per 100 percentage points), ``theta`` per year. ``OptionGreeks`` converts to
the per-point and per-day figures a broker screen shows.
"""

import math
from collections import namedtuple

__all__ = [
    "CALL",
    "PUT",
    "Greeks",
    "normalize_right",
    "intrinsic",
    "bsm",
    "black76",
    "binomial",
    "implied_vol",
]

CALL, PUT = "C", "P"

Greeks = namedtuple("Greeks", "price delta gamma vega theta rho")

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def normalize_right(right):
    """``"C"`` or ``"P"`` for any spelling of call or put."""
    key = str(right).strip().upper()
    if key in ("C", "CALL"):
        return CALL
    if key in ("P", "PUT"):
        return PUT
    raise ValueError(f"an option right is a call or a put, not {right!r}")


def _cdf(x):
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


def _pdf(x):
    return math.exp(-0.5 * x * x) / _SQRT2PI


def intrinsic(right, S, K):
    """What the option is worth exercised now: max(S - K, 0) or max(K - S, 0)."""
    if normalize_right(right) == CALL:
        return max(S - K, 0.0)
    return max(K - S, 0.0)


def bsm(right, S, K, T, r, sigma, q=0.0):
    """Black-Scholes-Merton for a European option on an asset paying a
    continuous yield ``q``. Returns ``Greeks``.

    At or past expiry (``T <= 0``) the price is the intrinsic value. With no
    volatility it is the discounted payoff on the forward."""
    call = normalize_right(right) == CALL
    phi = 1.0 if call else -1.0
    if T <= 0.0:
        price = intrinsic(right, S, K)
        delta = phi if phi * (S - K) > 0.0 else 0.0
        return Greeks(price, delta, 0.0, 0.0, 0.0, 0.0)

    dq, dr = math.exp(-q * T), math.exp(-r * T)
    if sigma <= 0.0:
        fwd = phi * (S * dq - K * dr)
        itm = fwd > 0.0
        price = fwd if itm else 0.0
        delta = phi * dq if itm else 0.0
        theta = phi * (q * S * dq - r * K * dr) if itm else 0.0
        rho = phi * K * T * dr if itm else 0.0
        return Greeks(price, delta, 0.0, 0.0, theta, rho)

    sqt = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqt)
    d2 = d1 - sigma * sqt
    nd1 = _pdf(d1)
    Nd1, Nd2 = _cdf(phi * d1), _cdf(phi * d2)

    price = phi * (S * dq * Nd1 - K * dr * Nd2)
    if price <= 0.0:  # rounding far out of the money; max() would keep -0.0
        price = 0.0
    delta = phi * dq * Nd1
    gamma = dq * nd1 / (S * sigma * sqt)
    vega = S * dq * nd1 * sqt
    theta = -S * dq * nd1 * sigma / (2.0 * sqt) + phi * (
        q * S * dq * Nd1 - r * K * dr * Nd2
    )
    rho = phi * K * T * dr * Nd2
    return Greeks(price, delta, gamma, vega, theta, rho)


def black76(right, F, K, T, r, sigma):
    """Black-76 for a European option on a futures price ``F``. Returns
    ``Greeks``; ``delta`` and ``gamma`` are with respect to ``F``."""
    g = bsm(right, F, K, T, r, sigma, q=r)
    return g._replace(rho=-T * g.price if T > 0.0 else 0.0)


def binomial(right, S, K, T, r, sigma, q=0.0, steps=200, american=True):
    """Price on a Cox-Ross-Rubinstein tree of ``steps`` steps. ``american``
    allows exercise at every node; ``False`` prices the European option,
    which converges to ``bsm`` as ``steps`` grows."""
    if T <= 0.0 or sigma <= 0.0 or steps < 1:
        return bsm(right, S, K, T, r, sigma, q).price

    phi = 1.0 if normalize_right(right) == CALL else -1.0
    dt = T / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    disc = math.exp(-r * dt)
    p = (math.exp((r - q) * dt) - d) / (u - d)
    if not 0.0 < p < 1.0:
        raise ValueError("too few steps for this rate and volatility")

    values = [
        max(phi * (S * u**j * d ** (steps - j) - K), 0.0) for j in range(steps + 1)
    ]
    for n in range(steps - 1, -1, -1):
        for j in range(n + 1):
            cont = disc * (p * values[j + 1] + (1.0 - p) * values[j])
            if american:
                cont = max(cont, phi * (S * u**j * d ** (n - j) - K))
            values[j] = cont
    return values[0]


def implied_vol(
    price, right, S, K, T, r, q=0.0, model="bsm", lo=1e-4, hi=5.0, tol=1e-10, **kw
):
    """The volatility at which ``model`` reproduces ``price``, or ``NaN`` when
    no volatility in ``[lo, hi]`` does (a price below intrinsic value, for
    instance). ``model`` is ``"bsm"``, ``"black76"`` (``S`` is then the
    futures price and ``q`` is ignored) or ``"binomial"`` (extra keywords
    such as ``steps`` and ``american`` are passed on)."""
    if T <= 0.0 or not math.isfinite(price):
        return math.nan

    if model == "bsm":

        def value(sig):
            g = bsm(right, S, K, T, r, sig, q)
            return g.price, g.vega

    elif model == "black76":

        def value(sig):
            g = black76(right, S, K, T, r, sig)
            return g.price, g.vega

    elif model == "binomial":
        # below this the tree's up-probability leaves (0, 1)
        dt = T / kw.get("steps", 200)
        lo = max(lo, 1.01 * abs(r - q) * math.sqrt(dt) + 1e-6)

        def value(sig):
            return binomial(right, S, K, T, r, sig, q, **kw), 0.0

    else:
        raise ValueError(f"unknown model {model!r}")

    a, b = lo, hi
    fa = value(a)[0] - price
    fb = value(b)[0] - price
    if fa > 0.0 or fb < 0.0:
        return math.nan  # outside what any volatility in [lo, hi] produces
    if fa > -tol:
        # the lowest volatility already reproduces the price, so every low
        # one does: a worthless option identifies no volatility
        return math.nan

    sig = min(max(0.2, a), b)
    for _ in range(200):
        p, vega = value(sig)
        diff = p - price
        if abs(diff) < tol:
            return sig
        if diff > 0.0:
            b = sig
        else:
            a = sig
        step = sig - diff / vega if vega > 1e-12 else None
        sig = step if step is not None and a < step < b else 0.5 * (a + b)
        if b - a < tol:
            break
    return sig
