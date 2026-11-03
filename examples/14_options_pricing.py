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
"""Option pricing on its own: prices, greeks, implied volatility.

``bt.options.pricing`` needs no data feed and no cerebro. Inputs are the
right ("C"/"P"), the underlying price, the strike, the years to expiry,
the interest rate and the volatility (rates and volatilities as fractions:
0.05 is 5%).

The first numbers are the worked examples in Hull, *Options, Futures, and
Other Derivatives*, to compare against.

Run it:  python examples/14_options_pricing.py [--plot]
"""

import math
import sys

from backtrader.options import pricing

REQUIRES = ()


def main(plot=False):
    # European options on a stock (Black-Scholes-Merton)
    call = pricing.bsm("C", S=42, K=40, T=0.5, r=0.10, sigma=0.20)
    put = pricing.bsm("P", S=42, K=40, T=0.5, r=0.10, sigma=0.20)
    print(f"call {call.price:.2f}, put {put.price:.2f}   (Hull: 4.76 and 0.81)")

    # put-call parity: c - p = S - K e^{-rT}
    parity = 42 - 40 * math.exp(-0.10 * 0.5)
    print(f"c - p = {call.price - put.price:.4f} = S - K e^-rT = {parity:.4f}")

    # the greeks, in textbook units (vega and rho per 1.00, theta per year)
    g = pricing.bsm("C", S=49, K=50, T=20 / 52, r=0.05, sigma=0.20)
    print(
        f"delta {g.delta:.3f}  gamma {g.gamma:.3f}  vega {g.vega:.1f}  "
        f"theta {g.theta:.2f}  rho {g.rho:.2f}"
    )
    print(
        f"  per volatility point: vega {g.vega / 100:.3f}; per day: theta {g.theta / 365:.4f}"
    )

    # an option on a futures price (Black-76)
    fut = pricing.black76("P", F=20, K=20, T=4 / 12, r=0.09, sigma=0.25)
    print(f"futures put {fut.price:.2f}   (Hull: 1.12)")

    # an American put on a binomial tree, against its European twin
    for steps in (5, 50, 500):
        a = pricing.binomial("P", S=50, K=50, T=5 / 12, r=0.10, sigma=0.40, steps=steps)
        print(f"American put, {steps:3d} steps: {a:.3f}")
    e = pricing.bsm("P", S=50, K=50, T=5 / 12, r=0.10, sigma=0.40).price
    print(f"European put:            {e:.3f}  (the early-exercise premium is the gap)")

    # implied volatility: the volatility at which the model gives a price
    market = 5.10
    iv = pricing.implied_vol(market, "C", S=100, K=100, T=0.25, r=0.03)
    print(
        f"a 3-month at-the-money call trading at {market} implies {iv:.2%} volatility"
    )
    smile = [
        (K, pricing.implied_vol(p, "P", S=100, K=K, T=0.25, r=0.03))
        for K, p in ((85, 0.60), (90, 1.20), (95, 2.30), (100, 4.10))
    ]
    print("put prices into a skew: " + ", ".join(f"K={K} {v:.1%}" for K, v in smile))

    if plot:
        import matplotlib.pyplot as plt

        strikes = range(70, 131, 5)
        spot = 100.0
        calls = [
            pricing.bsm("C", S=spot, K=k, T=0.25, r=0.03, sigma=0.20).price
            for k in strikes
        ]
        puts = [
            pricing.bsm("P", S=spot, K=k, T=0.25, r=0.03, sigma=0.20).price
            for k in strikes
        ]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        ax1.plot(strikes, calls, label="Call (T=0.25, σ=20%)", color="tab:blue")
        ax1.plot(strikes, puts, label="Put (T=0.25, σ=20%)", color="tab:orange")
        ax1.axvline(
            spot, color="gray", linestyle="--", alpha=0.7, label=f"Spot ({spot:.0f})"
        )
        ax1.set_xlabel("Strike")
        ax1.set_ylabel("Option Price")
        ax1.set_title("BSM Option Pricing Curve")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        smile_k = [x[0] for x in smile]
        smile_iv = [x[1] * 100 for x in smile]
        ax2.plot(
            smile_k, smile_iv, marker="o", color="tab:red", label="Implied Volatility"
        )
        ax2.set_xlabel("Strike")
        ax2.set_ylabel("Implied Volatility (%)")
        ax2.set_title("Put Volatility Skew")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
