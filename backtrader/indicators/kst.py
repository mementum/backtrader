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
from . import SMA, ROC100


class KnowSureThing(bt.Indicator):
    '''
    Martin Pring 开发并于 1992 年在 *Stocks & Commodities* 发表的
    "summed" momentum indicator。

    Args:
        rp1: 第 1 个 ROC100 周期。
        rp2: 第 2 个 ROC100 周期。
        rp3: 第 3 个 ROC100 周期。
        rp4: 第 4 个 ROC100 周期。
        rma1: 第 1 个 ROC 平滑周期。
        rma2: 第 2 个 ROC 平滑周期。
        rma3: 第 3 个 ROC 平滑周期。
        rma4: 第 4 个 ROC 平滑周期。
        rsignal: signal line 的平滑周期。
        rfactors: 应用于各个 MovAv(ROC) 的权重列表。
        _rmovav: 用于 ROC 平滑的 Moving Average 类型。
        _smovav: 用于 signal line 的 Moving Average 类型。

    Returns:
        KnowSureThing: 输出 ``kst`` 与 ``signal`` line 的 indicator。

    Formula:
      - rcma1 = MovAv(roc100(rp1), period)
      - rcma2 = MovAv(roc100(rp2), period)
      - rcma3 = MovAv(roc100(rp3), period)
      - rcma4 = MovAv(roc100(rp4), period)

      - kst = 1.0 * rcma1 + 2.0 * rcma2 + 3.0 * rcma3 + 4.0 * rcma4
      - signal = MovAv(kst, speriod)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:know_sure_thing_kst

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(KnowSureThing)
    '''
    alias = ('KST',)
    lines = ('kst', 'signal',)
    params = (
        ('rp1', 10), ('rp2', 15), ('rp3', 20), ('rp4', 30),
        ('rma1', 10), ('rma2', 10), ('rma3', 10), ('rma4', 10),
        ('rsignal', 9),
        ('rfactors', [1.0, 2.0, 3.0, 4.0]),
        ('_rmovav', SMA),
        ('_smovav', SMA),
    )

    plotinfo = dict(plothlines=[0.0])

    def __init__(self):
        rcma1 = self.p._rmovav(ROC100(period=self.p.rp1), period=self.p.rma1)
        rcma2 = self.p._rmovav(ROC100(period=self.p.rp2), period=self.p.rma2)
        rcma3 = self.p._rmovav(ROC100(period=self.p.rp3), period=self.p.rma3)
        rcma4 = self.p._rmovav(ROC100(period=self.p.rp4), period=self.p.rma4)
        self.l.kst = sum([rfi * rci for rfi, rci in
                          zip(self.p.rfactors, [rcma1, rcma2, rcma3, rcma4])])

        self.l.signal = self.p._smovav(self.l.kst, period=self.p.rsignal)
        super(KnowSureThing, self).__init__()
