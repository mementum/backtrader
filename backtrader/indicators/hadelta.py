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


import backtrader as bt
from . import MovAv


__all__ = ['haDelta', 'haD']


class haDelta(bt.Indicator):
    '''Dan Valcu 在 *"Heikin-Ashi: How to Trade Without Candlestick Patterns"*
    中定义的 Heikin Ashi Delta。

    该 indicator 衡量 Heikin Ashi candle 的 close 与 open 之差，也就是 candle body。

    信号通常来自 3 周期 Moving Average 平滑后的 haDelta。

    若 ``autoheikin`` 为 False，传入数据应已经通过 Heikin Ashi filter 处理。

    Args:
        period: 平滑 haDelta 的 Moving Average 周期。
        movav: 用于平滑的 Moving Average 类型。
        autoheikin: 是否自动先计算 HeikinAshi 数据。

    Returns:
        haDelta: 输出 ``haDelta`` 与 ``smoothed`` line 的 indicator。

    Formula:
      - haDelta = Heikin Ashi close - Heikin Ashi open
      - smoothed = movav(haDelta, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(haDelta, period=3)
    '''
    alias = ('haD',)

    lines = ('haDelta', 'smoothed')

    params = (
        ('period', 3),
        ('movav', MovAv.SMA),
        ('autoheikin', True),
    )

    plotinfo = dict(subplot=True)

    plotlines = dict(
        haDelta=dict(color='red'),
        smoothed=dict(color='grey', _fill_gt=(0, 'green'), _fill_lt=(0, 'red'))
    )

    def __init__(self):
        d = bt.ind.HeikinAshi(self.data) if self.p.autoheikin else self.data

        self.lines.haDelta = hd = d.close - d.open
        self.lines.smoothed = self.p.movav(hd, period=self.p.period)
        super(haDelta, self).__init__()
