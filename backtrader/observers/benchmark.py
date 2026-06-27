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
from . import TimeReturn


class Benchmark(TimeReturn):
    '''存储 strategy return 和参考资产 return 的 observer。

    参考资产是传入系统的某个 data，用于和 strategy 表现进行对比。

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            报告整个 backtest period 的完整 return。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。
        data: 用于对比的参考资产，默认 ``None``。该 data 必须已经通过
            ``adddata``、``resampledata`` 或 ``replaydata`` 加入 ``cerebro``。
        _doprenext (bool): 是否从 data feed 起点就记录 benchmark，默认
            ``False``。默认情况下会从 strategy 最小 period 满足后开始记录。
        firstopen (bool): 默认 ``False``，确保第 1 个 value 与 benchmark 的
            比较点从 0% 开始。完整含义参见 ``TimeReturn`` analyzer。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        None: observer 通过 ``benchmark`` line 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(Benchmark)

    '''
    _stclock = True

    lines = ('benchmark',)
    plotlines = dict(benchmark=dict(_name='Benchmark'))

    params = (
        ('data', None),
        ('_doprenext', False),
        # 设为 False，确保资产在第 1 个 tick 以 0% 开始衡量
        ('firstopen', False),
        ('fund', None)
    )

    def _plotlabel(self):
        labels = super(Benchmark, self)._plotlabel()
        labels.append(self.p.data._name)
        return labels

    def __init__(self):
        if self.p.data is None:  # 未指定时使用系统中的第 1 个 data
            self.p.data = self.data0

        super(Benchmark, self).__init__()  # 包含 data 参数的 treturn
        # 创建不带 data 的 time return 对象
        kwargs = self.p._getkwargs()
        kwargs.update(data=None)  # 用于创建 strategy return
        t = self._owner._addanalyzer_slave(bt.analyzers.TimeReturn, **kwargs)

        # 交换以保持一致性
        self.treturn, self.tbench = t, self.treturn

    def next(self):
        super(Benchmark, self).next()
        self.lines.benchmark[0] = self.tbench.rets.get(self.treturn.dtkey,
                                                       float('NaN'))

    def prenext(self):
        if self.p._doprenext:
            super(TimeReturn, self).prenext()
