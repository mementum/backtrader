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


from . import MovingAverageBase, MovAv


# 继承 MovingAverageBase，以自动注册为 MovingAverage 类型
class HullMovingAverage(MovingAverageBase):
    '''Alan Hull 提出的 Hull Moving Average。

    HMA 尝试解决 Moving Average 既要更快响应当前价格活动、又要保持曲线平滑的难题。
    它几乎消除了 lag，同时提升了平滑效果。

    Args:
        period: 计算周期。
        _movav: 内部使用的 Moving Average 类型。

    Returns:
        HullMovingAverage: 输出 ``hma`` line 的 indicator。

    Formula:
      - hma = wma(2 * wma(data, period // 2) - wma(data, period), sqrt(period))

    See also:
      - http://alanhull.com/hull-moving-average

    Note:

      - 最终 minimum period 并不是参数 ``period`` 本身。最后还会对 moving average
        再做一次 moving average，其周期是原始周期的 *square root*。

        默认 ``30`` 的情况下，在 moving average 产出非 NAN 值前，最终 minimum
        period 为 ``34``。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(HullMovingAverage, period=30)
    '''
    alias = ('HMA', 'HullMA',)
    lines = ('hma',)

    # period 参数继承自 MovingAverageBase
    params = (('_movav', MovAv.WMA),)

    def __init__(self):
        wma = self.p._movav(self.data, period=self.params.period)
        wma2 = 2.0 * self.p._movav(self.data, period=self.params.period // 2)

        sqrtperiod = pow(self.params.period, 0.5)
        self.lines.hma = self.p._movav(wma2 - wma, period=int(sqrtperiod))

        # 计算后再调用，确保协作继承和组合可用
        super(HullMovingAverage, self).__init__()
