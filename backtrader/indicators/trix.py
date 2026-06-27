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

from . import Indicator, MovAv


class Trix(Indicator):
    '''
    Jack Hutson 在 20 世纪 80 年代定义，用于显示三重指数平滑 Moving Average 的
    Rate of Change (%) 或斜率。

    Args:
        period: EMA 平滑周期。
        _rocperiod: 计算 Rate of Change 的回看周期。
        _movav: 用于平滑的 Moving Average 类型。

    Returns:
        Trix: 输出 ``trix`` line 的 indicator。

    Formula:
      - ema1 = EMA(data, period)
      - ema2 = EMA(ema1, period)
      - ema3 = EMA(ema2, period)
      - trix = 100 * (ema3 - ema3(-1)) / ema3(-1)

      最终公式可简化为：100 * (ema3 / ema3(-1) - 1)

    默认使用 EMA 作为 Moving Average。

    See:
      - https://en.wikipedia.org/wiki/Trix_(technical_analysis)
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:trix

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Trix, period=15)
    '''
    alias = ('TRIX',)
    lines = ('trix',)
    params = (('period', 15), ('_rocperiod', 1), ('_movav', MovAv.EMA),)

    plotinfo = dict(plothlines=[0.0])

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p._rocperiod] * self.p.notdefault('_rocperiod')
        plabels += [self.p._movav] * self.p.notdefault('_movav')
        return plabels

    def __init__(self):

        ema1 = self.p._movav(self.data, period=self.p.period)
        ema2 = self.p._movav(ema1, period=self.p.period)
        ema3 = self.p._movav(ema2, period=self.p.period)

        # 1 周期 Percentage Rate of Change
        self.lines.trix = 100.0 * (ema3 / ema3(-self.p._rocperiod) - 1.0)

        super(Trix, self).__init__()


class TrixSignal(Trix):
    '''
    Trix 的扩展版本，额外添加类似 MACD 的 signal line。

    Args:
        period: EMA 平滑周期。
        sigperiod: signal line 的平滑周期。
        _rocperiod: 计算 Rate of Change 的回看周期。
        _movav: 用于平滑的 Moving Average 类型。

    Returns:
        TrixSignal: 输出 ``trix`` 与 ``signal`` line 的 indicator。

    Formula:
      - trix = Trix(data, period)
      - signal = EMA(trix, sigperiod)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:trix

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(TrixSignal, period=15, sigperiod=9)
    '''
    lines = ('signal',)
    params = (('sigperiod', 9),)

    def __init__(self):
        super(TrixSignal, self).__init__()

        self.l.signal = self.p._movav(self.lines[0], period=self.p.sigperiod)
