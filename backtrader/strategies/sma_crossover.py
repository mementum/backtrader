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


import backtrader as bt
import backtrader.indicators as btind


class MA_CrossOver(bt.Strategy):
    '''基于 moving average cross 的 long-only strategy。

    当 fast moving average 向上穿越 slow moving average 且当前没有 position 时买入；
    当 fast moving average 向下穿越 slow moving average 且当前已有 position 时卖出。

    Args:
        fast: fast moving average 的 period。
        slow: slow moving average 的 period。
        _movav: 使用的 moving average 类，默认 ``btind.MovAv.SMA``。

    Returns:
        MA_CrossOver: 使用 ``Market`` order 执行均线交叉信号的 strategy。

    ---
    交互示例：
        >>> import backtrader as bt
        >>> from backtrader.strategies import MA_CrossOver
        >>> cerebro = bt.Cerebro()
        >>> cerebro.addstrategy(MA_CrossOver, fast=5, slow=20)
        0

    '''
    alias = ('SMA_CrossOver',)

    params = (
        # fast Moving Average 的 period
        ('fast', 10),
        # slow Moving Average 的 period
        ('slow', 30),
        # 使用的 moving average
        ('_movav', btind.MovAv.SMA)
    )

    def __init__(self):
        sma_fast = self.p._movav(period=self.p.fast)
        sma_slow = self.p._movav(period=self.p.slow)

        self.buysig = btind.CrossOver(sma_fast, sma_slow)

    def next(self):
        if self.position.size:
            if self.buysig < 0:
                self.sell()

        elif self.buysig > 0:
            self.buy()
