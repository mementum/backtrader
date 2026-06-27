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
from backtrader.utils.py3 import itervalues
from backtrader.mathsupport import average, standarddev
from . import TimeReturn


__all__ = ['PeriodStats']


class PeriodStats(bt.Analyzer):
    '''计算给定 timeframe 的基础统计信息

    Args:
        timeframe: 统计使用的 timeframe，默认 ``Years``。如果为 ``None``，
            将使用系统中第 1 个 data 的 ``timeframe``。传入
            ``TimeFrame.NoTimeFrame`` 可在不受时间约束的情况下考虑整个
            dataset。
        compression (int): timeframe 压缩倍数，默认 ``1``。仅用于日内
            timeframe。例如指定 ``TimeFrame.Minutes`` 并将 compression 设为
            60，即可按小时 timeframe 工作。如果为 ``None``，将使用系统中第
            1 个 data 的 compression。
        zeroispos (bool): 如果设为 ``True``，无变化的 period 会被计为正数。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 是基于总净资产 value 还是 fund
            value。参见 broker 文档中的 ``set_fundmode``。将其设为 ``True``
            或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回一个包含以下 key 的字典:

      - ``average``
      - ``stddev``
      - ``positive``
      - ``negative``
      - ``nochange``
      - ``best``
      - ``worst``

    ---
    交互示例:

    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(PeriodStats, timeframe=bt.TimeFrame.Years)
    >>> # 运行后可通过 strategy.analyzers 中的 analyzer 调用 get_analysis()
    '''

    params = (
        ('timeframe', bt.TimeFrame.Years),
        ('compression', 1),
        ('zeroispos', False),
        ('fund', None),
    )

    def __init__(self):
        self._tr = TimeReturn(timeframe=self.p.timeframe,
                              compression=self.p.compression, fund=self.p.fund)

    def stop(self):
        trets = self._tr.get_analysis()  # dict key = date, value = ret
        pos = nul = neg = 0
        trets = list(itervalues(trets))
        for tret in trets:
            if tret > 0.0:
                pos += 1
            elif tret < 0.0:
                neg += 1
            else:
                if self.p.zeroispos:
                    pos += tret == 0.0
                else:
                    nul += tret == 0.0

        self.rets['average'] = avg = average(trets)
        self.rets['stddev'] = standarddev(trets, avg)

        self.rets['positive'] = pos
        self.rets['negative'] = neg
        self.rets['nochange'] = nul

        self.rets['best'] = max(trets)
        self.rets['worst'] = min(trets)
