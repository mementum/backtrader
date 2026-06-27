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

from . import MovingAverageBase, ExponentialSmoothing


class SmoothedMovingAverage(MovingAverageBase):
    '''
    Wilder 在 1978 年 *New Concepts in Technical Trading* 中使用的
    Smoothing Moving Average。

    Args:
        period: 平滑周期。

    Returns:
        SmoothedMovingAverage: 输出 ``smma`` line 的 indicator。

    书中的原始定义为：

      - new_value = (old_value * (period - 1) + new_data) / period

    可用下列因子表示为 ``SmoothingMovingAverage``：

      - self.smfactor -> 1.0 / period
      - self.smfactor1 -> `1.0 - self.smfactor`

    Formula:
      - movav = prev * (1.0 - smoothfactor) + newdata * smoothfactor

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Modified_moving_average

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(SmoothedMovingAverage, period=20)
    '''
    alias = ('SMMA', 'WilderMA', 'MovingAverageSmoothed',
             'MovingAverageWilder', 'ModifiedMovingAverage',)
    lines = ('smma',)

    def __init__(self):
        # 放在 super 之前，确保 mixin（子类化时右侧基类）能看到赋值操作并处理该 line
        self.lines[0] = ExponentialSmoothing(
            self.data,
            period=self.p.period,
            alpha=1.0 / self.p.period)
        super(SmoothedMovingAverage, self).__init__()
