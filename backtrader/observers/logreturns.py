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


__all__ = ['LogReturns', 'LogReturns2']


class LogReturns(bt.Observer):
    '''存储 strategy 或 data 的 *log returns* 的 observer。

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            报告整个 backtest period 的完整 return。传入
            ``TimeFrame.NoTimeFrame`` 可在不受时间约束的情况下考虑整个
            dataset。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        None: observer 通过 ``logret1`` line 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(LogReturns)

    '''
    _stclock = True

    lines = ('logret1',)
    plotinfo = dict(plot=True, subplot=True)

    params = (
        ('timeframe', None),
        ('compression', None),
        ('fund', None),
    )

    def _plotlabel(self):
        return [bt.TimeFrame.getname(self.p.timeframe, self.p.compression),
                str(self.p.compression or 1)]

    def __init__(self):
        self.logret1 = self._owner._addanalyzer_slave(
            bt.analyzers.LogReturnsRolling,
            data=self.data0, **self.p._getkwargs())

    def next(self):
        self.lines.logret1[0] = self.logret1.rets[self.logret1.dtkey]


class LogReturns2(LogReturns):
    '''扩展 ``LogReturns``，用于显示两个 instrument。

    Args:
        继承 ``LogReturns`` 的参数。

    Returns:
        None: observer 通过 ``logret1`` 和 ``logret2`` lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(LogReturns2)
    '''
    lines = ('logret2',)

    def __init__(self):
        super(LogReturns2, self).__init__()

        self.logret2 = self._owner._addanalyzer_slave(
            bt.analyzers.LogReturnsRolling,
            data=self.data1, **self.p._getkwargs())

    def next(self):
        super(LogReturns2, self).next()
        self.lines.logret2[0] = self.logret2.rets[self.logret2.dtkey]
