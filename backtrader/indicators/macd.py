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


class MACD(Indicator):
    '''
    Gerald Appel 在 20 世纪 70 年代定义的 Moving Average Convergence Divergence。

    它衡量短期与长期 Moving Average 之间的距离，用于尝试识别趋势。

    对 convergence-divergence 再做一次滞后 Moving Average，可在被 macd 穿越时
    提供 "signal"。

    Args:
        period_me1: 短周期 Moving Average 周期。
        period_me2: 长周期 Moving Average 周期。
        period_signal: signal line 的平滑周期。
        movav: 用于计算的 Moving Average 类型。

    Returns:
        MACD: 输出 ``macd`` 与 ``signal`` line 的 indicator。

    Formula:
      - macd = ema(data, me1_period) - ema(data, me2_period)
      - signal = ema(macd, signal_period)

    See:
      - http://en.wikipedia.org/wiki/MACD

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(MACD)
    '''
    lines = ('macd', 'signal',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9),
              ('movav', MovAv.Exponential),)

    plotinfo = dict(plothlines=[0.0])
    plotlines = dict(signal=dict(ls='--'))

    def _plotlabel(self):
        plabels = super(MACD, self)._plotlabel()
        if self.p.isdefault('movav'):
            plabels.remove(self.p.movav)
        return plabels

    def __init__(self):
        super(MACD, self).__init__()
        me1 = self.p.movav(self.data, period=self.p.period_me1)
        me2 = self.p.movav(self.data, period=self.p.period_me2)
        self.lines.macd = me1 - me2
        self.lines.signal = self.p.movav(self.lines.macd,
                                         period=self.p.period_signal)


class MACDHisto(MACD):
    '''
    MACD 的子类，额外添加 macd 与 signal line 差值的 "histogram"。

    Args:
        period_me1: 短周期 Moving Average 周期。
        period_me2: 长周期 Moving Average 周期。
        period_signal: signal line 的平滑周期。
        movav: 用于计算的 Moving Average 类型。

    Returns:
        MACDHisto: 输出 ``macd``、``signal`` 与 ``histo`` line 的 indicator。

    Formula:
      - histo = macd - signal

    See:
      - http://en.wikipedia.org/wiki/MACD

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(MACDHisto)
    '''
    alias = ('MACDHistogram',)

    lines = ('histo',)
    plotlines = dict(histo=dict(_method='bar', alpha=0.50, width=1.0))

    def __init__(self):
        super(MACDHisto, self).__init__()
        self.lines.histo = self.lines.macd - self.lines.signal
