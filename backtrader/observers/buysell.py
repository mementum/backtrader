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

from __future__ import absolute_import, division, print_function, unicode_literals

import math

from .. import lineiterator


class BuySellObserver(object):
    def __init__(self, datas):
        for data in datas:
            _BuySellObserver(data)


class _BuySellObserver(lineiterator.LineObserver):
    lines = ('buy', 'sell',)

    plotinfo = dict(subplot=False, linelabels=True)
    plotlines = dict(
        buy=dict(marker='^', markersize=8.0, color='g', fillstyle='none'),
        sell=dict(marker='v', markersize=8.0, color='r', fillstyle='none')
    )

    def __init__(self):
        self.data = self.datas[0]

    def next(self):
        buy = list()
        sell = list()

        for order in self._owner._orderspending:
            if order.data != self.data or not order.executed.size:
                continue

            if order.isbuy():
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

        # Write down the average buy/sell price
        self.lines.buy = math.fsum(buy)/float(len(buy) or 'NaN')
        self.lines.sell = math.fsum(sell)/float(len(sell) or 'NaN')
