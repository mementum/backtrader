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

from . import Indicator, And


class NonZeroDifference(Indicator):
    '''
    跟踪两个输入 data 的差值；当前差值为 0 时，沿用上一个非 0 差值。

    Args:
        data0: 第一个 data。
        data1: 第二个 data。

    Returns:
        NonZeroDifference: 输出 ``nzd`` line 的 indicator。

    Formula:
      - diff = data - data1
      - nzd = diff if diff else diff(-1)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(NonZeroDifference)
    '''
    _mindatas = 2  # 需要两个 data source
    alias = ('NZD',)
    lines = ('nzd',)

    def nextstart(self):
        self.l.nzd[0] = self.data0[0] - self.data1[0]  # 种子值

    def next(self):
        d = self.data0[0] - self.data1[0]
        self.l.nzd[0] = d if d else self.l.nzd[-1]

    def oncestart(self, start, end):
        self.line.array[start] = (
            self.data0.array[start] - self.data1.array[start])

    def once(self, start, end):
        d0array = self.data0.array
        d1array = self.data1.array
        larray = self.line.array

        prev = larray[start - 1]
        for i in range(start, end):
            d = d0array[i] - d1array[i]
            larray[i] = prev = d if d else prev


class _CrossBase(Indicator):
    '''交叉判断的基类，用于实现向上/向下穿越的共同逻辑。'''

    _mindatas = 2

    lines = ('cross',)

    plotinfo = dict(plotymargin=0.05, plotyhlines=[0.0, 1.0])

    def __init__(self):
        nzd = NonZeroDifference(self.data0, self.data1)

        if self._crossup:
            before = nzd(-1) < 0.0  # data0 之前在下方或等于 0
            after = self.data0 > self.data1
        else:
            before = nzd(-1) > 0.0  # data0 之前在上方或等于 0
            after = self.data0 < self.data1

        self.lines.cross = And(before, after)


class CrossUp(_CrossBase):
    '''
    当第一个 data 向上穿越第二个 data 时给出信号。

    Args:
        data0: 第一个 data。
        data1: 第二个 data。

    Returns:
        CrossUp: 输出 ``cross`` line 的向上穿越 indicator。

    会查看两个 data 的当前索引 ``0`` 和前一索引 ``-1``。

    Formula:
      - diff = data - data1
      - upcross =  last_non_zero_diff < 0 and data0(0) > data1(0)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(CrossUp)
    '''
    _crossup = True


class CrossDown(_CrossBase):
    '''
    当第一个 data 向下穿越第二个 data 时给出信号。

    Args:
        data0: 第一个 data。
        data1: 第二个 data。

    Returns:
        CrossDown: 输出 ``cross`` line 的向下穿越 indicator。

    会查看两个 data 的当前索引 ``0`` 和前一索引 ``-1``。

    Formula:
      - diff = data - data1
      - downcross = last_non_zero_diff > 0 and data0(0) < data1(0)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(CrossDown)
    '''
    _crossup = False


class CrossOver(Indicator):
    '''
    当两个 data 向上或向下穿越时给出信号。

      - 1.0 if the 1st data crosses the 2nd data upwards
      - -1.0 if the 1st data crosses the 2nd data downwards

    Args:
        data0: 第一个 data。
        data1: 第二个 data。

    Returns:
        CrossOver: 输出 ``crossover`` line 的 indicator；向上穿越为 ``1.0``，
        向下穿越为 ``-1.0``。

    会查看两个 data 的当前索引 ``0`` 和前一索引 ``-1``。

    Formula:
      - diff = data - data1
      - upcross =  last_non_zero_diff < 0 and data0(0) > data1(0)
      - downcross = last_non_zero_diff > 0 and data0(0) < data1(0)
      - crossover = upcross - downcross

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(CrossOver)
    '''
    _mindatas = 2

    lines = ('crossover',)

    plotinfo = dict(plotymargin=0.05, plotyhlines=[-1.0, 1.0])

    def __init__(self):
        upcross = CrossUp(self.data, self.data1)
        downcross = CrossDown(self.data, self.data1)

        self.lines.crossover = upcross - downcross
