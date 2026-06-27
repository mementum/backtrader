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

from . import PeriodN


__all__ = ['HurstExponent', 'Hurst']


class HurstExponent(PeriodN):
    '''
    Hurst Exponent 指标，用于判断序列更接近随机游走、均值回归还是趋势状态。

    Args:
        period: 计算窗口周期。
        lag_start: lag 起始值；为空时使用 ``2``。
        lag_end: lag 结束值；为空时使用 ``self.p.period / 2``。

    Returns:
        HurstExponent: 输出 ``hurst`` line 的 indicator。

    References:

      - https://www.quantopian.com/posts/hurst-exponent
      - https://www.quantopian.com/posts/some-code-from-ernie-chans-new-book-implemented-in-python

    结果解释：

      1. Geometric random walk (H=0.5)
      2. Mean-reverting series (H<0.5)
      3. Trending series (H>0.5)

    重要说明：

      - 默认 period 为 ``40``，但用户实验表明至少使用 2000 个样本（即 period 至少
        2000）更容易得到稳定值。

      - 未指定参数时，``lag_start`` 和 ``lag_end`` 默认分别为 ``2`` 和
        ``self.p.period / 2``。

        用户实验也表明，约 ``10`` 和 ``500`` 的取值表现较好。

    原始取值 ``(40, 2, self.p.period / 2)`` 为保持向后兼容而保留。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(HurstExponent, period=2000)
    '''
    frompackages = (
        ('numpy', ('asarray', 'log10', 'polyfit', 'sqrt', 'std', 'subtract')),
    )

    alias = ('Hurst',)
    lines = ('hurst',)
    params = (
        ('period', 40),  # 曾建议使用 2000
        ('lag_start', None),  # 曾建议使用 10
        ('lag_end', None),  # 曾建议使用 500
    )

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self._lag_start]
        plabels += [self._lag_end]
        return plabels

    def __init__(self):
        super(HurstExponent, self).__init__()
        # 准备 lags 数组
        self._lag_start = lag_start = self.p.lag_start or 2
        self._lag_end = lag_end = self.p.lag_end or (self.p.period // 2)
        self.lags = asarray(range(lag_start, lag_end))
        self.log10lags = log10(self.lags)

    def next(self):
        # 获取数据
        ts = asarray(self.data.get(size=self.p.period))

        # 计算 lagged differences 的方差数组
        tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in self.lags]

        # 使用线性拟合估算 Hurst Exponent
        poly = polyfit(self.log10lags, log10(tau), 1)

        # 从 polyfit 输出中返回 Hurst exponent
        self.lines.hurst[0] = poly[0] * 2.0
