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

from . import Indicator, And, If, MovAv, ATR


class UpMove(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中作为 Directional Move System 的一部分定义，用于计算
    Directional Indicator。

    当给定 data 高于前一日时为正。

    Args:
        data: 用于比较的 line。

    Returns:
        UpMove: 输出 ``upmove`` line 的 indicator。

    Formula:
      - upmove = data - data(-1)

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(UpMove)
    '''
    lines = ('upmove',)

    def __init__(self):
        self.lines.upmove = self.data - self.data(-1)
        super(UpMove, self).__init__()


class DownMove(Indicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中作为 Directional Move System 的一部分定义，用于计算
    Directional Indicator。

    当给定 data 低于前一日时为正。

    Args:
        data: 用于比较的 line。

    Returns:
        DownMove: 输出 ``downmove`` line 的 indicator。

    Formula:
      - downmove = data(-1) - data

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DownMove)
    '''
    lines = ('downmove',)

    def __init__(self):
        self.lines.downmove = self.data(-1) - self.data
        super(DownMove, self).__init__()


class _DirectionalIndicator(Indicator):
    '''
    Directional Movement System 相关 indicator 的根基类，用于承载公共计算。

    它可根据参数提示计算 +DI 和 -DI，但不直接赋给 line；具体赋值由子类完成。
    '''
    params = (('period', 14), ('movav', MovAv.Smoothed))

    plotlines = dict(plusDI=dict(_name='+DI'), minusDI=dict(_name='-DI'))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self, _plus=True, _minus=True):
        atr = ATR(self.data, period=self.p.period, movav=self.p.movav)

        upmove = self.data.high - self.data.high(-1)
        downmove = self.data.low(-1) - self.data.low

        if _plus:
            plus = And(upmove > downmove, upmove > 0.0)
            plusDM = If(plus, upmove, 0.0)
            plusDMav = self.p.movav(plusDM, period=self.p.period)

            self.DIplus = 100.0 * plusDMav / atr

        if _minus:
            minus = And(downmove > upmove, downmove > 0.0)
            minusDM = If(minus, downmove, 0.0)
            minusDMav = self.p.movav(minusDM, period=self.p.period)

            self.DIminus = 100.0 * minusDMav / atr

        super(_DirectionalIndicator, self).__init__()


class DirectionalIndicator(_DirectionalIndicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中定义的 Directional Indicator。

    用于衡量趋势强度。

    该 indicator 显示 +DI、-DI：
      - 使用 PlusDirectionalIndicator (PlusDI) 获取 +DI
      - 使用 MinusDirectionalIndicator (MinusDI) 获取 -DI
      - 使用 AverageDirectionalIndex (ADX) 获取 ADX
      - 使用 AverageDirectionalIndexRating (ADXR) 获取 ADX、ADXR
      - 使用 DirectionalMovementIndex (DMI) 获取 ADX、+DI、-DI
      - 使用 DirectionalMovement (DM) 获取 ADX、ADXR、+DI、-DI

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        DirectionalIndicator: 输出 ``plusDI`` 与 ``minusDI`` line 的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DirectionalIndicator)
    '''
    alias = ('DI',)
    lines = ('plusDI', 'minusDI',)

    def __init__(self):
        super(DirectionalIndicator, self).__init__()

        self.lines.plusDI = self.DIplus
        self.lines.minusDI = self.DIminus


class PlusDirectionalIndicator(_DirectionalIndicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年定义的 +DI indicator。

    用于衡量趋势强度。

    该 indicator 显示 +DI。

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        PlusDirectionalIndicator: 输出 ``plusDI`` line 的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PlusDirectionalIndicator)
    '''
    alias = (('PlusDI', '+DI'),)
    lines = ('plusDI',)

    plotinfo = dict(plotname='+DirectionalIndicator')

    def __init__(self):
        super(PlusDirectionalIndicator, self).__init__(_minus=False)

        self.lines.plusDI = self.DIplus


class MinusDirectionalIndicator(_DirectionalIndicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年定义的 -DI indicator。

    用于衡量趋势强度。

    该 indicator 显示 -DI。

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        MinusDirectionalIndicator: 输出 ``minusDI`` line 的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - -di = 100 * MovingAverage(-dm, period) / atr(period)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(MinusDirectionalIndicator)
    '''
    alias = (('MinusDI', '-DI'),)
    lines = ('minusDI',)

    plotinfo = dict(plotname='-DirectionalIndicator')

    def __init__(self):
        super(MinusDirectionalIndicator, self).__init__(_plus=False)

        self.lines.minusDI = self.DIminus


class AverageDirectionalMovementIndex(_DirectionalIndicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年定义的 Average Directional Movement Index。

    用于衡量趋势强度。

    该 indicator 只显示 ADX。

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        AverageDirectionalMovementIndex: 输出 ``adx`` line 的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AverageDirectionalMovementIndex)
    '''
    alias = ('ADX',)

    lines = ('adx',)

    plotlines = dict(adx=dict(_name='ADX'))

    def __init__(self):
        super(AverageDirectionalMovementIndex, self).__init__()

        dx = abs(self.DIplus - self.DIminus) / (self.DIplus + self.DIminus)
        self.lines.adx = 100.0 * self.p.movav(dx, period=self.p.period)


class AverageDirectionalMovementIndexRating(AverageDirectionalMovementIndex):
    '''
    J. Welles Wilder, Jr. 于 1978 年定义的 ADXR。

    用于衡量趋势强度。

    ADXR 是当前 ADX 与 ``period`` 个 bar 之前 ADX 的平均值。

    该 indicator 显示 ADX 与 ADXR。

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        AverageDirectionalMovementIndexRating: 输出 ``adx`` 与 ``adxr`` line
        的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)
      - adxr = (adx + adx(-period)) / 2

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AverageDirectionalMovementIndexRating)
    '''
    alias = ('ADXR',)

    lines = ('adxr',)
    plotlines = dict(adxr=dict(_name='ADXR'))

    def __init__(self):
        super(AverageDirectionalMovementIndexRating, self).__init__()

        self.lines.adxr = (self.l.adx + self.l.adx(-self.p.period)) / 2.0


class DirectionalMovementIndex(AverageDirectionalMovementIndex,
                               DirectionalIndicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年定义的 Directional Movement Index。

    用于衡量趋势强度。

    该 indicator 显示 ADX、+DI 与 -DI。

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        DirectionalMovementIndex: 输出 ``adx``、``plusDI`` 与 ``minusDI`` line
        的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DirectionalMovementIndex)
    '''
    alias = ('DMI',)


class DirectionalMovement(AverageDirectionalMovementIndexRating,
                          DirectionalIndicator):
    '''
    J. Welles Wilder, Jr. 于 1978 年定义的完整 Directional Movement indicator。

    用于衡量趋势强度。

    该 indicator 显示 ADX、ADXR、+DI 与 -DI。

    Args:
        period: 计算周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        DirectionalMovement: 输出 ``adx``、``adxr``、``plusDI`` 与 ``minusDI``
        line 的 indicator。

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)

    默认 Moving Average 使用 Wilder 原始定义中的 SmoothedMovingAverage。

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DirectionalMovement)
    '''
    alias = ('DM',)
