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
from . import TimeDrawDown


__all__ = ['Calmar']


class Calmar(bt.TimeFrameAnalyzerBase):
    '''计算 Calmar Ratio 的 analyzer。

    统计使用的 timeframe 可以不同于底层 data 使用的 timeframe。

    Args:
        timeframe: 统计使用的 timeframe，默认 ``TimeFrame.Months``。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。如果为 ``None``，使用系统中第 1 个 data 的
            compression。
        period (int): rolling 计算使用的 period 数量，默认 ``36``。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        OrderedDict: ``get_analysis`` 返回以时间 period 为 key、rolling
        Calmar Ratio 为 value 的字典。

    Attributes:
        calmar: 最近一次计算得到的 Calmar Ratio。

    See also:
        https://en.wikipedia.org/wiki/Calmar_ratio

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(Calmar, timeframe=bt.TimeFrame.Months,
    ...                     period=36, _name='calmar')
    '''

    packages = ('collections', 'math',)

    params = (
        ('timeframe', bt.TimeFrame.Months),  # calmar 默认值
        ('period', 36),
        ('fund', None),
    )

    def __init__(self):
        self._maxdd = TimeDrawDown(timeframe=self.p.timeframe,
                                   compression=self.p.compression)

    def start(self):
        self._mdd = float('-inf')
        self._values = collections.deque([float('Nan')] * self.p.period,
                                         maxlen=self.p.period)
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        if not self._fundmode:
            self._values.append(self.strategy.broker.getvalue())
        else:
            self._values.append(self.strategy.broker.fundvalue)

    def on_dt_over(self):
        self._mdd = max(self._mdd, self._maxdd.maxdd)
        if not self._fundmode:
            self._values.append(self.strategy.broker.getvalue())
        else:
            self._values.append(self.strategy.broker.fundvalue)
        rann = math.log(self._values[-1] / self._values[0]) / len(self._values)
        self.calmar = calmar = rann / (self._mdd or float('Inf'))

        self.rets[self.dtkey] = calmar

    def stop(self):
        self.on_dt_over()  # 更新最后一组 value
