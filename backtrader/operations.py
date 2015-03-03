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
import datapos

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
    lines = ('buy', 'sell', 'position', 'pnl')

    def __init__(self):
        self.orders = collections.deque()
        self.lastpos = 0.0

        self.longs = 0
        self.shorts = 0
        self.position = datapos.Position()

    def addorder(self, order):
        self.orders.append(order)

    def next(self):
        buy = list()
        sell = list()

        curpos = 0
        while self.orders:
            order = self.orders.popleft()
            # ordpos = order.executed.position
            if not order.executed.size:
                continue # no size ... no execution

            if order.isbuy():
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

            if False:
                curpos = order.position
                if not self.lastpos:
                    if curpos > 0:
                        self.longs += 1
                        self.pos.update(order.executed.size, order.executed.price)
                    elif curpos < 0:
                        self.shorts += 1
                        self.pos.update(-order.executed.size, order.executed.price)

                elif self.lastpos > 0:
                    if curpos > self.lastpos:
                        # long position added to long position
                        # update only with extra seen
                        self.pos.update(curpos - self.lastpos, order.executed.price)
                    elif curpos > 0 and curpos <= self.lastpos:
                        # position has been reduced or is equal ...
                        # need to add pnl to this operation
                        pass
                    elif curpos == 0:
                        # position closed, add net profit/loss to line
                        # self.lines.pnl[0] = calculated profit and loss
                        pass

                    elif curpos < 0:
                        # position closed, add net profit/loss to line
                        # self.lines.pnl[0] = calculated profit and loss
                        # add a short
                        self.shorts += 1

                else: # self.lastpos < 0:
                    if curpos < self.lastpos:
                        # short position added to long position
                        # change average price
                        pass
                    elif curpos == 0:
                        # position closed, add net profit/loss to line
                        # self.lines.pnl[0] = calculated profit and loss
                        pass

                    elif curpos > 0:
                        # position closed, add net profit/loss to line
                        # self.lines.pnl[0] = calculated profit and loss
                        # add a long
                        self.longs += 1

            else:
                curpos = self.lastpos
                lastpost = curpos

        # Write down the average buy/sell price
        self.lines.buy[0] = math.fsum(buy)/float(len(buy) or 'NaN')
        self.lines.sell[0] = math.fsum(sell)/float(len(sell) or 'NaN')
        self.lines.position[0] = curpos
