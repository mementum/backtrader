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


from . import MovingAverageBase, MovAv, ZeroLagIndicator


class DicksonMovingAverage(MovingAverageBase):
    '''Nathan Dickson 提出的 Dickson Moving Average。

    *Dickson Moving Average* 结合 Ehlers 的 ``ZeroLagIndicator``（也称
    *ErrorCorrecting* 或 *EC*）与 ``HullMovingAverage``，尝试得到接近
    *Jurik* Moving Averages 的效果。

    Args:
        period: ZeroLagIndicator 的计算周期。
        gainlimit: ZeroLagIndicator 的增益上限。
        hperiod: HullMovingAverage 的计算周期。
        _movav: ZeroLagIndicator 使用的 Moving Average 类型。
        _hma: 第二个 Moving Average 类型，默认使用 HullMovingAverage。

    Returns:
        DicksonMovingAverage: 输出 ``dma`` line 的 Moving Average indicator。

    Formula:
      - ec = ZeroLagIndicator(period, gainlimit)
      - hma = HullMovingAverage(hperiod)

      - dma = (ec + hma) / 2

      - *ZeroLagIndicator* 默认使用 EMA，可通过参数 ``_movav`` 修改。

        .. note:: 传入的 Moving Average 必须计算 alpha（以及 1 - alpha），并以
                  ``alpha`` 与 ``alpha1`` 属性暴露。

      - 第 2 个 Moving Average 可通过参数 ``_hma`` 从 *Hull* 改为其他类型。

    See also:
      - https://www.reddit.com/r/algotrading/comments/4xj3vh/dickson_moving_average

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DicksonMovingAverage, period=30)
    '''
    alias = ('DMA', 'DicksonMA',)
    lines = ('dma',)
    params = (
        ('gainlimit', 50),
        ('hperiod', 7),
        ('_movav', MovAv.EMA),
        ('_hma', MovAv.HMA),
    )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.gainlimit, self.p.hperiod]
        plabels += [self.p._movav] * self.p.notdefault('_movav')
        plabels += [self.p._hma] * self.p.notdefault('_hma')
        return plabels

    def __init__(self):
        ec = ZeroLagIndicator(period=self.p.period,
                              gainlimit=self.p.gainlimit,
                              _movav=self.p._movav)

        hull = self.p._hma(period=self.p.hperiod)

        self.lines.dma = (ec + hull) / 2.0

        # 为了让 mixin 生效，将 super 放在末尾以支持协作式继承
        super(DicksonMovingAverage, self).__init__()
