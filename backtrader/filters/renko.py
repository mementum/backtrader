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


from . import Filter


__all__ = ['Renko']


class Renko(Filter):
    '''修改 data stream，用于绘制 Renko bars（bricks）的 filter。

    Args:
        hilo (bool): 是否使用 high/low 而不是 close 来判断是否需要新 brick，
            默认 ``False``。
        size: 每个 brick 使用的 size，默认 ``None``。
        autosize (float): ``size`` 为 ``None`` 时用于自动计算 brick size 的值，
            默认 ``20.0``。计算方式是用当前价格除以该值。
        dynamic (bool): 在使用 ``autosize`` 时，是否在移动到新 brick 时重新
            计算 brick size，默认 ``False``。启用后会破坏 Renko bricks 的
            完美对齐。
        align (float): 用于对齐 brick price 边界的 factor，默认 ``1.0``。
            例如 price 为 ``3563.25``、align 为 ``10.0`` 时，对齐结果为
            ``3560``:

          - 3563.25 / 10.0 = 356.325
          - round 并移除 decimals -> 356
          - 356 * 10.0 -> 3560

        roundstart (bool): 是否将初始 start value round 为 int，默认
            ``True``。设为 ``False`` 可在回测 penny stocks 时保留原始值。

    Returns:
        bool: 输出 Renko brick 时返回 ``False``；当前 bar 未形成新 brick 时
        回退 data 并返回 ``True``，表示 stream 长度改变，需要获取新 bar。

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:chart_analysis:renko

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='daily.csv')
    >>> data.addfilter(Renko, size=2.0, align=1.0)
    '''

    params = (
        ('hilo', False),
        ('size', None),
        ('autosize', 20.0),
        ('dynamic', False),
        ('align', 1.0),
        ('roundstart', True),
    )

    def nextstart(self, data):
        o = data.open[0]
        o = round(o / self.p.align, 0) * self.p.align  # 已对齐
        self._size = self.p.size or float(o // self.p.autosize)
        if self.p.roundstart:
            o = int(o)

        self._top = o + self._size
        self._bot = o - self._size

    def next(self, data):
        c = data.close[0]
        h = data.high[0]
        l = data.low[0]

        if self.p.hilo:
            hiprice = h
            loprice = l
        else:
            hiprice = loprice = c

        if hiprice >= self._top:
            # 输出一个从 top -> top + size 的 renko brick
            self._bot = bot = self._top

            if self.p.size is None and self.p.dynamic:
                self._size = float(c // self.p.autosize)
                top = bot + self._size
                top = round(top / self.p.align, 0) * self.p.align  # 已对齐
            else:
                top = bot + self._size

            self._top = top

            data.open[0] = bot
            data.low[0] = bot
            data.high[0] = top
            data.close[0] = top
            data.volume[0] = 0.0
            data.openinterest[0] = 0.0
            return False  # data stream 长度不变

        elif loprice <= self._bot:
            # 输出一个从 bot -> bot - size 的 renko brick
            self._top = top = self._bot

            if self.p.size is None and self.p.dynamic:
                self._size = float(c // self.p.autosize)
                bot = top - self._size
                bot = round(bot / self.p.align, 0) * self.p.align  # 已对齐
            else:
                bot = top - self._size

            self._bot = bot

            data.open[0] = top
            data.low[0] = top
            data.high[0] = bot
            data.close[0] = bot
            data.volume[0] = 0.0
            data.openinterest[0] = 0.0
            return False  # data stream 长度不变

        data.backwards()
        return True  # stream 长度已改变，获取新 bar
