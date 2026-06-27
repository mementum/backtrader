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
from .. import Observer


class DrawDown(Observer):
    '''跟踪当前 drawdown 和 maxdrawdown 的 observer。

    当前 drawdown 会被绘制，maxdrawdown 默认不绘制。

    Args:
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 drawdown 基于总净资产 value 还是 fund
            value。将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        None: observer 通过 ``drawdown`` 和 ``maxdrawdown`` lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(DrawDown)

    '''
    _stclock = True

    params = (
        ('fund', None),
    )

    lines = ('drawdown', 'maxdrawdown',)

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(maxdrawdown=dict(_plotskip=True,))

    def __init__(self):
        kwargs = self.p._getkwargs()
        self._dd = self._owner._addanalyzer_slave(bt.analyzers.DrawDown,
                                                  **kwargs)

    def next(self):
        self.lines.drawdown[0] = self._dd.rets.drawdown  # 更新 drawdown
        self.lines.maxdrawdown[0] = self._dd.rets.max.drawdown  # 更新最大值


class DrawDownLength(Observer):
    '''跟踪当前 drawdown length 和最大 drawdown length 的 observer。

    当前 drawdown length 会被绘制，最大 length 默认不绘制。

    Args:
        无。

    Returns:
        None: observer 通过 ``len`` 和 ``maxlen`` lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(DrawDownLength)
    '''
    _stclock = True

    lines = ('len', 'maxlen',)

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(maxlength=dict(_plotskip=True,))

    def __init__(self):
        self._dd = self._owner._addanalyzer_slave(bt.analyzers.DrawDown)

    def next(self):
        self.lines.len[0] = self._dd.rets.len  # 更新 drawdown length
        self.lines.maxlen[0] = self._dd.rets.max.len  # 更新最大 length


class DrawDown_Old(Observer):
    '''旧版 drawdown observer，跟踪当前 drawdown 和 maxdrawdown。

    Args:
        无。

    Returns:
        None: observer 通过 ``drawdown`` 和 ``maxdrawdown`` lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(DrawDown_Old)
    '''
    _stclock = True

    lines = ('drawdown', 'maxdrawdown',)

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(maxdrawdown=dict(_plotskip='True',))

    def __init__(self):
        super(DrawDown_Old, self).__init__()

        self.maxdd = 0.0
        self.peak = float('-inf')

    def next(self):
        value = self._owner.broker.getvalue()

        # 更新已见到的最大峰值
        if value > self.peak:
            self.peak = value

        # 计算当前 drawdown
        self.lines.drawdown[0] = dd = 100.0 * (self.peak - value) / self.peak

        # 按需更新 maxdrawdown
        self.lines.maxdrawdown[0] = self.maxdd = max(self.maxdd, dd)
