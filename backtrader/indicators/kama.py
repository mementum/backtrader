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

from . import (SumN, MovingAverageBase, ExponentialSmoothingDynamic)


class AdaptiveMovingAverage(MovingAverageBase):
    '''
    Perry Kaufman 在 *"Smarter Trading"* 中定义的 Adaptive Moving Average。

    该 Moving Average 会结合市场方向与波动性，持续缩放 smoothing factor。
    smoothing factor 来自两个 ExponentialMovingAverage 平滑因子：一个快周期，
    一个慢周期。

    当市场呈趋势状态时，数值会更接近快速 EMA 平滑周期；当市场缺乏趋势时，
    它会向慢速 EMA 平滑周期移动。

    它是 SmoothingMovingAverage 的子类，通过动态 smoothing factor 处理实时变化。

    Args:
        period: 计算方向与波动性的周期。
        fast: 快速 EMA 平滑周期。
        slow: 慢速 EMA 平滑周期。

    Returns:
        AdaptiveMovingAverage: 输出 ``kama`` line 的 Moving Average indicator。

    Formula:
      - direction = close - close_period
      - volatility = sumN(abs(close - close_n), period)
      - effiency_ratio = abs(direction / volatility)
      - fast = 2 / (fast_period + 1)
      - slow = 2 / (slow_period + 1)

      - smfactor = squared(efficienty_ratio * (fast - slow) + slow)
      - smfactor1 = 1.0  - smfactor

      - 初始种子值为 SimpleMovingAverage

    See also:
      - http://fxcodebase.com/wiki/index.php/Kaufman's_Adaptive_Moving_Average_(KAMA)
      - http://www.metatrader5.com/en/terminal/help/analytics/indicators/trend_indicators/ama
      - http://help.cqg.com/cqgic/default.htm#!Documents/adaptivemovingaverag2.htm

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AdaptiveMovingAverage, period=30)
    '''
    alias = ('KAMA', 'MovingAverageAdaptive',)
    lines = ('kama',)
    params = (('fast', 2), ('slow', 30))

    def __init__(self):
        # 放在 super 之前，确保 mixin（子类化时右侧基类）能看到赋值并处理该 line
        direction = self.data - self.data(-self.p.period)
        volatility = SumN(abs(self.data - self.data(-1)), period=self.p.period)

        er = abs(direction / volatility)  # efficiency ratio

        fast = 2.0 / (self.p.fast + 1.0)  # fast EMA smoothing factor
        slow = 2.0 / (self.p.slow + 1.0)  # slow EMA smoothing factor

        sc = pow((er * (fast - slow)) + slow, 2)  # 可缩放常量

        self.lines[0] = ExponentialSmoothingDynamic(self.data,
                                                    period=self.p.period,
                                                    alpha=sc)

        super(AdaptiveMovingAverage, self).__init__()
