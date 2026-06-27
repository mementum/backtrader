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

from backtrader import TimeFrameAnalyzerBase


class TimeReturn(TimeFrameAnalyzerBase):
    '''按指定 timeframe 计算 return 的 analyzer。

    该 analyzer 会比较每个 timeframe 起点和终点的 value，既可以跟踪
    portfolio/fund value，也可以跟踪指定 data 的价格变化。

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            使用系统中第 1 个 data 的 timeframe。传入
            ``TimeFrame.NoTimeFrame`` 可在不受时间约束的情况下考虑整个
            dataset。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。例如指定 ``TimeFrame.Minutes`` 并将 compression 设为
            60，即可按小时 timeframe 工作。如果为 ``None``，使用系统中第 1
            个 data 的 compression。
        data: 要跟踪的参考资产，默认 ``None``。如果为 ``None``，跟踪
            portfolio value 或 fund value。该 data 必须已经通过
            ``adddata``、``resampledata`` 或 ``replaydata`` 加入 ``cerebro``。
        firstopen (bool): 跟踪 data 且第 1 次计算没有前一根 close 时，是否用
            open 作为起始参考价，默认 ``True``。如果为 ``False``，使用初始
            close。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回以 datetime 为 key、return 为 value 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(TimeReturn, timeframe=bt.TimeFrame.Months,
    ...                     _name='timereturn')
    '''

    params = (
        ('data', None),
        ('firstopen', True),
        ('fund', None),
    )

    def start(self):
        super(TimeReturn, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        self._value_start = 0.0
        self._lastvalue = None
        if self.p.data is None:
            # 未跟踪 data 时，保留初始 portfolio value
            if not self._fundmode:
                self._lastvalue = self.strategy.broker.getvalue()
            else:
                self._lastvalue = self.strategy.broker.fundvalue

    def notify_fund(self, cash, value, fundvalue, shares):
        if not self._fundmode:
            # 记录当前 value
            if self.p.data is None:
                self._value = value  # 未跟踪 data 时为 portfolio value
            else:
                self._value = self.p.data[0]  # 跟踪 data 时为 data value
        else:
            if self.p.data is None:
                self._value = fundvalue  # 未跟踪 data 时为 fund value
            else:
                self._value = self.p.data[0]  # 跟踪 data 时为 data value

    def on_dt_over(self):
        # next 会在新的 timeframe period 中被调用
        # if self.p.data is None or len(self.p.data) > 1:
        if self.p.data is None or self._lastvalue is not None:
            self._value_start = self._lastvalue  # 将 value_start 更新为上次 value

        else:
            # 第 1 个 tick 没有前值引用，使用 opening price
            if self.p.firstopen:
                self._value_start = self.p.data.open[0]
            else:
                self._value_start = self.p.data[0]

    def next(self):
        # 计算 return
        super(TimeReturn, self).next()
        self.rets[self.dtkey] = (self._value / self._value_start) - 1.0
        self._lastvalue = self._value  # 保留上次 value
