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


from . import Indicator, MovAv, ATR


class PrettyGoodOscillator(Indicator):
    '''
    Mark Johnson 提出的 "Pretty Good Oscillator" (PGO)，用于衡量当前 close
    与同周期 Simple Moving Average 的距离，并用同类周期的 Average True Range
    表达该距离。

    例如 PGO 为 +2.5，表示当前 close 高于 SMA 的距离约为 2.5 个平均日内波幅。

    Johnson 的用法偏向较长期的突破系统：PGO 上穿 3.0 可做多，下穿 -3.0 可做空，
    两种情况下都在回到 0（即 close 回到 SMA 附近）时退出。

    Args:
        period: 计算 Moving Average 与 ATR 的周期。
        _movav: 用于计算中线的 Moving Average 类型。

    Returns:
        PrettyGoodOscillator: 输出 ``pgo`` line 的 indicator。

    Formula:
      - pgo = (data.close - sma(data, period)) / atr(data, period)

    See also:
      - http://user42.tuxfamily.org/chart/manual/Pretty-Good-Oscillator.html

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PrettyGoodOscillator, period=14)
    '''
    alias = ('PGO', 'PrettyGoodOsc',)
    lines = ('pgo',)

    params = (('period', 14), ('_movav', MovAv.Simple),)

    def __init__(self):
        movav = self.p._movav(self.data, period=self.p.period)
        atr = ATR(self.data, period=self.p.period)

        self.lines.pgo = (self.data - movav) / atr
        super(PrettyGoodOscillator, self).__init__()
