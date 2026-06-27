#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

from ..observer import Observer


class BuySell(Observer):
    '''跟踪单笔 buy/sell execution，并在图上标出执行价附近位置的 observer。

    Args:
        barplot (bool): 是否把 buy 信号画在 bar 最低价下方、sell 信号画在最高价
            上方，默认 ``False``。如果为 ``False``，会画在该 bar 内 execution
            的平均价上。
        bardist (float): ``barplot`` 为 ``True`` 时，距离最高/最低价的比例，
            默认 ``0.015``（1.5%）。

    Returns:
        None: observer 通过 ``buy`` 和 ``sell`` lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(BuySell, barplot=True)
    '''
    lines = ('buy', 'sell',)

    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        buy=dict(marker='^', markersize=8.0, color='lime',
                 fillstyle='full', ls=''),
        sell=dict(marker='v', markersize=8.0, color='red',
                  fillstyle='full', ls='')
    )

    params = (
        ('barplot', False),  # bar plot 中画在最高/最低价之外以增强可读性
        ('bardist', 0.015),  # 到最高/最低价的绝对比例距离
    )

    def next(self):
        buy = list()
        sell = list()

        for order in self._owner._orderspending:
            if order.data is not self.data or not order.executed.size:
                continue

            if order.isbuy():
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

        # 考虑 replay 场景：line 中可能已有值
        # 写入平均 buy/sell price

        # BUY
        curbuy = self.lines.buy[0]
        if curbuy != curbuy:  # NaN
            curbuy = 0.0
            self.curbuylen = curbuylen = 0
        else:
            curbuylen = self.curbuylen

        buyops = (curbuy + math.fsum(buy))
        buylen = curbuylen + len(buy)

        value = buyops / float(buylen or 'NaN')
        if not self.p.barplot:
            self.lines.buy[0] = value
        elif value == value:  # 不是 NaN
            pbuy = self.data.low[0] * (1 - self.p.bardist)
            self.lines.buy[0] = pbuy

        # 更新 buylen 值
        curbuy = buyops
        self.curbuylen = buylen

        # SELL
        cursell = self.lines.sell[0]
        if cursell != cursell:  # NaN
            cursell = 0.0
            self.curselllen = curselllen = 0
        else:
            curselllen = self.curselllen

        sellops = (cursell + math.fsum(sell))
        selllen = curselllen + len(sell)

        value = sellops / float(selllen or 'NaN')
        if not self.p.barplot:
            self.lines.sell[0] = value
        elif value == value:  # 不是 NaN
            psell = self.data.high[0] * (1 + self.p.bardist)
            self.lines.sell[0] = psell

        # 更新 selllen 值
        cursell = sellops
        self.curselllen = selllen
