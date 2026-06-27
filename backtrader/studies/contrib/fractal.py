#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
# (based on backtrader from Daniel Rodriguez)
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

import backtrader as bt


__all__ = ['Fractal']


class Fractal(bt.ind.PeriodN):
    '''Fractal indicator。

    在指定 period 内，如果最高 high 位于中心且两侧 high 更低，则标记 bearish
    fractal；如果最低 low 位于中心且两侧 low 更高，则标记 bullish fractal。

    Args:
        period: 判断 fractal pattern 使用的 bar 数量。
        bardist: 绘制 marker 时相对 high/low 的偏移百分比。
        shift_to_potential_fractal: 中心候选 bar 相对窗口的位置。

    Returns:
        Fractal: 输出 ``fractal_bearish`` 与 ``fractal_bullish`` 两条 line 的
        indicator。

    References:
        [Ref 1] http://www.investopedia.com/articles/trading/06/fractals.asp

    ---
    交互示例：
        >>> from backtrader.studies.contrib.fractal import Fractal
        >>> Fractal.params.period
        5

    '''
    lines = ('fractal_bearish', 'fractal_bullish')

    plotinfo = dict(subplot=False, plotlinelabels=False, plot=True)

    plotlines = dict(
        fractal_bearish=dict(marker='^', markersize=4.0, color='lightblue',
                             fillstyle='full', ls=''),
        fractal_bullish=dict(marker='v', markersize=4.0, color='lightblue',
                             fillstyle='full', ls='')
    )
    params = (
        ('period', 5),
        ('bardist', 0.015),  # 到 max/min 的绝对百分比距离
        ('shift_to_potential_fractal', 2),
    )

    def next(self):
        # bearish turning point：最高 high 位于中间，两侧各有两个更低 high。[Ref 1]

        last_five_highs = self.data.high.get(size=self.p.period)
        max_val = max(last_five_highs)
        max_idx = last_five_highs.index(max_val)

        if max_idx == self.p.shift_to_potential_fractal:
            self.lines.fractal_bearish[-2] = max_val * (1 + self.p.bardist)

        # bullish turning point：最低 low 位于中间，两侧各有两个更高 low。[Ref 1]
        last_five_lows = self.data.low.get(size=self.p.period)
        min_val = min(last_five_lows)
        min_idx = last_five_lows.index(min_val)

        if min_idx == self.p.shift_to_potential_fractal:
            self.l.fractal_bullish[-2] = min_val * (1 - self.p.bardist)
