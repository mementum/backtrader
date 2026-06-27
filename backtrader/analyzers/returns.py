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

import math

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase


class Returns(TimeFrameAnalyzerBase):
    '''使用 logarithmic 方法计算总收益、平均收益、复合收益和年化收益。

    参考:

      - https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            使用系统中第 1 个 data 的 timeframe。传入
            ``TimeFrame.NoTimeFrame`` 可在不受时间约束的情况下考虑整个
            dataset。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。例如指定 ``TimeFrame.Minutes`` 并将 compression 设为
            60，即可按小时 timeframe 工作。如果为 ``None``，使用系统中第 1
            个 data 的 compression。
        tann: 年化（normalization）使用的 period 数量，默认 ``None``。如果
            未指定，会按 timeframe 使用默认值: days=252、weeks=52、
            months=12、years=1。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回包含以下 key 的字典:

      - ``rtot``: 总复合 return
      - ``ravg``: 整个 period 的平均 return（与 timeframe 相关）
      - ``rnorm``: 年化/标准化 return
      - ``rnorm100``: 以 100% 表示的年化/标准化 return

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(Returns, timeframe=bt.TimeFrame.Years,
    ...                     _name='returns')

    '''

    params = (
        ('tann', None),
        ('fund', None),
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def start(self):
        super(Returns, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        if not self._fundmode:
            self._value_start = self.strategy.broker.getvalue()
        else:
            self._value_start = self.strategy.broker.fundvalue

        self._tcount = 0

    def stop(self):
        super(Returns, self).stop()

        if not self._fundmode:
            self._value_end = self.strategy.broker.getvalue()
        else:
            self._value_end = self.strategy.broker.fundvalue

        # 复合 return
        try:
            nlrtot = self._value_end / self._value_start
        except ZeroDivisionError:
            rtot = float('-inf')
        else:
            if nlrtot < 0.0:
                rtot = float('-inf')
            else:
                rtot = math.log(nlrtot)

        self.rets['rtot'] = rtot

        # 平均 return
        self.rets['ravg'] = ravg = rtot / self._tcount

        # 年化标准化 return
        tann = self.p.tann or self._TANN.get(self.timeframe, None)
        if tann is None:
            tann = self._TANN.get(self.data._timeframe, 1.0)  # 指派默认值

        if ravg > float('-inf'):
            self.rets['rnorm'] = rnorm = math.expm1(ravg * tann)
        else:
            self.rets['rnorm'] = rnorm = ravg

        self.rets['rnorm100'] = rnorm * 100.0  # 更便于阅读的百分比

    def _on_dt_over(self):
        self._tcount += 1  # 统计 subperiod
