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
from backtrader.utils.py3 import MAXINT


from . import MovingAverageBase, MovAv


class ZeroLagIndicator(MovingAverageBase):
    '''John Ehlers 与 Ric Way 提出的 ZeroLagIndicator。

    zero-lag indicator（ZLIndicator）是 EMA 的变体，通过最小化误差
    （price 与 error correction 的距离）来修正 EMA，从而降低滞后。

    Args:
        period: EMA 计算周期。
        gainlimit: 搜索 error correction factor 的增益上限。
        _movav: 用于计算基础 EMA 的 Moving Average 类型。

    Returns:
        ZeroLagIndicator: 输出 ``ec`` line 的 Moving Average indicator。

    Formula:
      - EMA(data, period)

      - 每轮遍历 ``-bestgain`` -> ``+bestgain``（含两端），为 EMA 计算最佳
        error correction。

      - 默认 Moving Average 为 EMA，可通过参数 ``_movav`` 修改。

        .. note:: 传入的 Moving Average 必须计算 alpha（以及 1 - alpha），并在
                  实例上以 ``alpha`` 和 ``alpha1`` 属性暴露。

    See also:
      - http://www.mesasoftware.com/papers/ZeroLag.pdf

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ZeroLagIndicator, period=30)
    '''
    alias = ('ZLIndicator', 'ZLInd', 'EC', 'ErrorCorrecting',)
    lines = ('ec',)
    params = (
        ('gainlimit', 50),
        ('_movav', MovAv.EMA),
    )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.gainlimit]
        plabels += [self.p._movav] * self.p.notdefault('_movav')
        return plabels

    def __init__(self):
        self.ema = MovAv.EMA(period=self.p.period)
        self.limits = [-self.p.gainlimit, self.p.gainlimit + 1]

        # 为了让 mixin 生效，将 super 放在末尾以支持协作式继承
        super(ZeroLagIndicator, self).__init__()

    def next(self):
        leasterror = MAXINT  # 原始代码中为 1000000
        bestec = ema = self.ema[0]  # ec 首次计算时的种子值
        price = self.data[0]
        ec1 = self.lines.ec[-1]
        alpha, alpha1 = self.ema.alpha, self.ema.alpha1

        for value1 in range(*self.limits):
            gain = value1 / 10
            ec = alpha * (ema + gain * (price - ec1)) + alpha1 * ec1
            error = abs(price - ec)
            if error < leasterror:
                leasterror = error
                bestec = ec

        self.lines.ec[0] = bestec
