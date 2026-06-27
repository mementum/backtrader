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


class _PriceOscBase(Indicator):
    '''Price Oscillator 的基类，用于统一短/长 Moving Average 差值计算。'''
    params = (('period1', 12), ('period2', 26),
              ('_movav', MovAv.Exponential),)

    plotinfo = dict(plothlines=[0.0])

    def __init__(self):
        self.ma1 = self.p._movav(self.data, period=self.p.period1)
        self.ma2 = self.p._movav(self.data, period=self.p.period2)
        self.lines[0] = self.ma1 - self.ma2

        super(_PriceOscBase, self).__init__()


class PriceOscillator(_PriceOscBase):
    '''
    显示短周期与长周期 Exponential Moving Average 的差值，以点数表达。

    Args:
        period1: 短周期 Moving Average 周期。
        period2: 长周期 Moving Average 周期。
        _movav: 用于计算的 Moving Average 类型。

    Returns:
        PriceOscillator: 输出 ``po`` line 的 indicator。

    Formula:
      - po = ema(short) - ema(long)

    See:
      - http://www.metastock.com/Customer/Resources/TAAZ/?c=3&p=94

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PriceOscillator)
    '''
    alias = ('PriceOsc', 'AbsolutePriceOscillator', 'APO', 'AbsPriceOsc',)
    lines = ('po',)


class PercentagePriceOscillator(_PriceOscBase):
    '''
    显示短周期与长周期 Exponential Moving Average 的差值，以百分比表达。
    MACD 做的是类似计算，但以绝对点数表达。

    用百分比表达差值，可以在底层价格水平差异很大时比较不同时点的指标值。

    Args:
        period1: 短周期 Moving Average 周期。
        period2: 长周期 Moving Average 周期。
        period_signal: signal line 的平滑周期。
        _movav: 用于计算的 Moving Average 类型。

    Returns:
        PercentagePriceOscillator: 输出 ``ppo``、``signal`` 与 ``histo`` line
        的 indicator。

    Formula:
      - po = 100 * (ema(short) - ema(long)) / ema(long)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:price_oscillators_ppo

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PercentagePriceOscillator)
    '''
    _long = True

    alias = ('PPO', 'PercPriceOsc',)

    lines = ('ppo', 'signal', 'histo')
    params = (('period_signal', 9),)

    plotlines = dict(histo=dict(_method='bar', alpha=0.50, width=1.0))

    def __init__(self):
        super(PercentagePriceOscillator, self).__init__()

        den = self.ma2 if self._long else self.ma1

        self.lines.ppo = 100.0 * self.lines[0] / den
        self.l.signal = self.p._movav(self.l.ppo, period=self.p.period_signal)
        self.lines.histo = self.lines.ppo - self.lines.signal


class PercentagePriceOscillatorShort(PercentagePriceOscillator):
    '''
    PercentagePriceOscillator 的短周期分母版本，以短周期 EMA 作为百分比计算分母。

    用百分比表达差值，可以在底层价格水平差异很大时比较不同时点的指标值。

    大部分在线资料使用长周期 EMA 作为分母；MetaStock 等资料使用短周期 EMA。

    Args:
        period1: 短周期 Moving Average 周期。
        period2: 长周期 Moving Average 周期。
        period_signal: signal line 的平滑周期。
        _movav: 用于计算的 Moving Average 类型。

    Returns:
        PercentagePriceOscillatorShort: 输出 ``ppo``、``signal`` 与 ``histo``
        line 的 indicator。

    Formula:
      - po = 100 * (ema(short) - ema(long)) / ema(short)

    See:
      - http://www.metastock.com/Customer/Resources/TAAZ/?c=3&p=94

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PercentagePriceOscillatorShort)
    '''
    _long = False
    alias = ('PPOShort', 'PercPriceOscShort',)
