#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
# Copyright (C) 2026 Dennis Hansen
#
# This file is part of slim-backtrader, a modified version of backtrader.
# Modified in 2026 by Dennis Hansen. See changelog.txt for the changes.
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

import backtrader as bt


class GrossLeverage(bt.Analyzer):
    """This analyzer calculates the Gross Leverage of the current strategy
    on a timeframe basis: the notional of every open position, long or
    short, over the value of the account.

    A position's notional is ``abs(size) * close * mult``: what a stock
    position is worth, a futures contract's full value rather than its
    margin, an option's premium times its multiplier. 0.0 is all cash, 1.0
    a fully invested long book, 2.0 a book long and short 100% each.

    Methods:

      - get_analysis

        Returns a dictionary with the leverage as values and the datetime
        points as keys
    """

    def next(self):
        broker = self.strategy.broker
        gross = 0.0
        for data, position in broker.positions.items():
            if position.size:
                mult = broker.getcommissioninfo(data).p.mult
                gross += abs(position.size) * data.close[0] * mult
        value = broker.getvalue()
        self.rets[self.data0.datetime.datetime()] = gross / value if value else 0.0
