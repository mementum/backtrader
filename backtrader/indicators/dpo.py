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
# Python 2/3 兼容导入
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator, MovAv


class DetrendedPriceOscillator(Indicator):
    '''
    Joe DiNapoli 在 *"Trading with DiNapoli levels"* 中定义的 DPO 指标。

    它衡量价格相对 Moving Average（趋势）的变化，从而从价格中移除“趋势”因素。

    Args:
        period: Moving Average 周期。
        movav: 使用的 Moving Average 类型。

    Returns:
        DetrendedPriceOscillator: 输出 ``dpo`` line 的 indicator。

    Formula:
      - movav = MovingAverage(close, period)
      - dpo = close - movav(shifted period / 2 + 1)

    See:
      - http://en.wikipedia.org/wiki/Detrended_price_oscillator

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DetrendedPriceOscillator, period=20)
    '''
    # 用于调用的命名别名
    alias = ('DPO',)

    # 命名输出 line
    lines = ('dpo',)

    # 可接受参数及默认值；movav 也作为参数，便于实验
    params = (('period', 20), ('movav', MovAv.Simple))

    # 绘图时强调中心 0.0 线
    plotinfo = dict(plothlines=[0.0])

    # indicator 名称后的信息（括号中）
    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        # 创建 Moving Average
        ma = self.p.movav(self.data, period=self.p.period)

        # 计算值（在 MA 中回看 period/2 + 1），并绑定到 dpo line
        self.lines.dpo = self.data - ma(-self.p.period // 2 + 1)

        super(DetrendedPriceOscillator, self).__init__()
