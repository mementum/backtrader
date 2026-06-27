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

from . import Indicator, Max, MovAv
from . import DivZeroByZero


class UpDay(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中为 RSI 定义的 UpDay。

    记录 "up" day，即 close 高于前一日的情况。

    Args:
        period: 比较前值的回看周期。

    Returns:
        UpDay: 输出 ``upday`` line 的 indicator。

    Formula:
      - upday = max(close - close_prev, 0)

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(UpDay)
    '''
    lines = ('upday',)
    params = (('period', 1),)

    def __init__(self):
        self.lines.upday = Max(self.data - self.data(-self.p.period), 0.0)
        super(UpDay, self).__init__()


class DownDay(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中为 RSI 定义的 DownDay。

    记录 "down" day，即 close 低于前一日的情况。

    Args:
        period: 比较前值的回看周期。

    Returns:
        DownDay: 输出 ``downday`` line 的 indicator。

    Formula:
      - downday = max(close_prev - close, 0)

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DownDay)
    '''
    lines = ('downday',)
    params = (('period', 1),)

    def __init__(self):
        self.lines.downday = Max(self.data(-self.p.period) - self.data, 0.0)
        super(DownDay, self).__init__()


class UpDayBool(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中为 RSI 定义的布尔版 UpDay。

    记录 "up" day，即 close 高于前一日的情况。

    Args:
        period: 比较前值的回看周期。

    Returns:
        UpDayBool: 输出布尔型 ``upday`` line 的 indicator。

    Note:
      - 该版本返回 bool，而不是差值。

    Formula:
      - upday = close > close_prev

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(UpDayBool)
    '''
    lines = ('upday',)
    params = (('period', 1),)

    def __init__(self):
        self.lines.upday = self.data > self.data(-self.p.period)
        super(UpDayBool, self).__init__()


class DownDayBool(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中为 RSI 定义的布尔版 DownDay。

    记录 "down" day，即 close 低于前一日的情况。

    Args:
        period: 比较前值的回看周期。

    Returns:
        DownDayBool: 输出布尔型 ``downday`` line 的 indicator。

    Note:
      - 该版本返回 bool，而不是差值。

    Formula:
      - downday = close_prev > close

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DownDayBool)
    '''
    lines = ('downday',)
    params = (('period', 1),)

    def __init__(self):
        self.lines.downday = self.data(-self.p.period) > self.data
        super(DownDayBool, self).__init__()


class RelativeStrengthIndex(Indicator):
    '''J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中定义的 Relative Strength Index。

    它先对上涨 close 与下跌 close 进行平均平滑，再计算二者比例，用 0 到 100
    的范围表达 momentum。

    Args:
        period: RSI 平滑周期。
        movav: 用于平滑 up/down day 的 Moving Average 类型。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。
        safediv: 是否处理 ``0 / 0`` 与 ``x / 0`` 的特殊除法情况。
        safehigh: ``x / 0`` 时使用的 RSI 值。
        safelow: ``0 / 0`` 时使用的 RSI 值。
        lookback: up/down day 比较的回看周期。

    Returns:
        RelativeStrengthIndex: 输出 ``rsi`` line 的 indicator。

    Formula:
      - up = upday(data)
      - down = downday(data)
      - maup = movingaverage(up, period)
      - madown = movingaverage(down, period)
      - rs = maup / madown
      - rsi = 100 - 100 / (1 + rs)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    Notes:
      - ``safediv`` 为 True 时，会检查 ``rs = maup / madown`` 中可能出现的
        ``0 / 0`` 或 ``x / 0`` 特殊情况。

      - ``safehigh`` 会作为 ``x / 0`` 情况下的 RSI 值。

      - ``safelow`` 会作为 ``0 / 0`` 情况下的 RSI 值。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RelativeStrengthIndex, period=14)
    '''
    alias = ('RSI', 'RSI_SMMA', 'RSI_Wilder',)

    lines = ('rsi',)
    params = (
        ('period', 14),
        ('movav', MovAv.Smoothed),
        ('upperband', 70.0),
        ('lowerband', 30.0),
        ('safediv', False),
        ('safehigh', 100.0),
        ('safelow', 50.0),
        ('lookback', 1),
    )

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        plabels += [self.p.lookback] * self.p.notdefault('lookback')
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):
        upday = UpDay(self.data, period=self.p.lookback)
        downday = DownDay(self.data, period=self.p.lookback)
        maup = self.p.movav(upday, period=self.p.period)
        madown = self.p.movav(downday, period=self.p.period)
        if not self.p.safediv:
            rs = maup / madown
        else:
            highrs = self._rscalc(self.p.safehigh)
            lowrs = self._rscalc(self.p.safelow)
            rs = DivZeroByZero(maup, madown, highrs, lowrs)

        self.lines.rsi = 100.0 - 100.0 / (1.0 + rs)
        super(RelativeStrengthIndex, self).__init__()

    def _rscalc(self, rsi):
        try:
            rs = (-100.0 / (rsi - 100.0)) - 1.0
        except ZeroDivisionError:
            return float('inf')

        return rs


class RSI_Safe(RSI):
    '''
    RSI 的子类，将 ``safediv`` 默认值改为 ``True``。

    Args:
        period: RSI 平滑周期。
        movav: 用于平滑 up/down day 的 Moving Average 类型。
        lookback: up/down day 比较的回看周期。

    Returns:
        RSI_Safe: 输出 ``rsi`` line 的安全除法版 RSI indicator。

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RSI_Safe)
    '''
    params = (('safediv', True),)


class RSI_SMA(RSI):
    '''
    使用 Wikipedia 和其他资料中描述的 SimpleMovingAverage 版本 RSI。

    Args:
        period: RSI 平滑周期。
        lookback: up/down day 比较的回看周期。

    Returns:
        RSI_SMA: 输出 ``rsi`` line 的 SimpleMovingAverage 版 RSI indicator。

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RSI_SMA)
    '''
    alias = ('RSI_Cutler',)

    params = (('movav', MovAv.Simple),)


class RSI_EMA(RSI):
    '''
    使用 Wikipedia 中描述的 ExponentialMovingAverage 版本 RSI。

    Args:
        period: RSI 平滑周期。
        lookback: up/down day 比较的回看周期。

    Returns:
        RSI_EMA: 输出 ``rsi`` line 的 ExponentialMovingAverage 版 RSI indicator。

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RSI_EMA)
    '''
    params = (('movav', MovAv.Exponential),)
