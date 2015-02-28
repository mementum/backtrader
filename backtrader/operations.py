#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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
################################################################################
import collections
import math

import lineiterator
import order as ordmod


class CashObserver(lineiterator.LineObserver):
    lines = ('cash',)

    def next(self):
        self.lines[0][0] = self._owner.broker.getcash()


class ValueObserver(lineiterator.LineObserver):
    lines = ('value',)

    def next(self):
        self.lines[0][0] = self._owner.broker.getvalue()


class CashValueObserver(lineiterator.LineObserver):
    lines = ('cash', 'value')

    def next(self):
        self.lines[0][0] = self._owner.broker.getcash()
        self.lines[1][0] = self._owner.broker.getvalue()


class ValueObserver(lineiterator.LineObserver):
    lines = ('value',)

    def next(self):
        self.lines.value = self._owner.broker.getvalue()


class Operations(lineiterator.LineObserver):
    lines = ('buy', 'sell', 'position')

    def __init__(self):
        self.orders = collections.deque()

    def addorder(self, order):
        self.orders.append(order)

    def prenext(self):
        self.lines.position = 0.0

    def next(self):
        buy = list()
        sell = list()
        lastpos = self.lines.position[-1]

        while self.orders:
            order = self.orders.popleft()
            # ordpos = order.executed.position
            if not order.executed.size:
                continue # no size ... no execution

            # Need to determine operation nature ... a buy is not necessarily a "long"
            # a "long" is having opened a positive operation from a previous pos <= 0
            # and viceversa for short

            if isinstance(order, ordmod.BuyOrder):
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

            # lastpos = order.executed.position

        self.lines.buy[0] = math.fsum(buy)/float(len(buy) or 'NaN')
        self.lines.sell[0] = math.fsum(sell)/float(len(sell) or 'NaN')
        self.lines.position[0] = lastpos
