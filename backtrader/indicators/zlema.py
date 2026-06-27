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


from . import Indicator, MovingAverageBase, MovAv


class ZeroLagExponentialMovingAverage(MovingAverageBase):
    '''
    Zero-lag Exponential Moving Average（ZLEMA）是 EMA 的变体。

    它加入 momentum 项来降低平均值滞后，使其更贴近当前价格。

    Args:
        period: 平滑周期。
        _movav: 用于内部计算的 Moving Average 类型。

    Returns:
        ZeroLagExponentialMovingAverage: 输出 ``zlema`` line 的 indicator。

    Formula:
      - lag = (period - 1) / 2
      - zlema = ema(2 * data - data(-lag))

    See also:
      - http://user42.tuxfamily.org/chart/manual/Zero_002dLag-Exponential-Moving-Average.html

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ZeroLagExponentialMovingAverage, period=20)
    '''
    alias = ('ZLEMA', 'ZeroLagEma',)
    lines = ('zlema',)
    params = (('_movav', MovAv.EMA),)

    def __init__(self):
        lag = (self.p.period - 1) // 2
        data = 2 * self.data - self.data(-lag)
        self.lines.zlema = self.p._movav(data, period=self.p.period)

        super(ZeroLagExponentialMovingAverage, self).__init__()
