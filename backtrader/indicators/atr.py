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

from . import Indicator, Max, Min, MovAv


class TrueHigh(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中为 ATR 定义的 TrueHigh。

    记录 "true high"，即今日 high 与昨日 close 的较大值。

    Args:
        data: 含有 high 与 close line 的数据源。

    Returns:
        TrueHigh: 输出 ``truehigh`` line 的 indicator。

    Formula:
      - truehigh = max(high, close_prev)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(TrueHigh)
    '''
    lines = ('truehigh',)

    def __init__(self):
        self.lines.truehigh = Max(self.data.high, self.data.close(-1))
        super(TrueHigh, self).__init__()


class TrueLow(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中为 ATR 定义的 TrueLow。

    记录 "true low"，即今日 low 与昨日 close 的较小值。

    Args:
        data: 含有 low 与 close line 的数据源。

    Returns:
        TrueLow: 输出 ``truelow`` line 的 indicator。

    Formula:
      - truelow = min(low, close_prev)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(TrueLow)
    '''
    lines = ('truelow',)

    def __init__(self):
        self.lines.truelow = Min(self.data.low, self.data.close(-1))
        super(TrueLow, self).__init__()


class TrueRange(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *New Concepts in Technical Trading
    Systems* 中定义的 TrueRange。

    它会纳入前一根 bar 的 close；当隔夜跳空使真实区间大于日内
    High-Low 时，可以反映更完整的 range。

    Args:
        data: 含有 high/low/close line 的数据源。

    Returns:
        TrueRange: 输出 ``tr`` line 的 indicator。

    Formula:
      - max(high - low, abs(high - prev_close), abs(prev_close - low)

      可简化为：

      - max(high, prev_close) - min(low, prev_close)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(TrueRange)
    '''
    alias = ('TR',)

    lines = ('tr',)

    def __init__(self):
        self.lines.tr = TrueHigh(self.data) - TrueLow(self.data)
        super(TrueRange, self).__init__()


class AverageTrueRange(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中定义的 Average True Range。

    它会纳入 close 来计算 range；当真实区间大于日内 High-Low 时，可以反映更完整的
    波动范围。

    Args:
        period: 平滑 TrueRange 的周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        AverageTrueRange: 输出 ``atr`` line 的 indicator。

    Formula:
      - SmoothedMovingAverage(TrueRange, period)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AverageTrueRange, period=14)
    '''
    alias = ('ATR',)

    lines = ('atr',)
    params = (('period', 14), ('movav', MovAv.Smoothed))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        self.lines.atr = self.p.movav(TR(self.data), period=self.p.period)
        super(AverageTrueRange, self).__init__()
