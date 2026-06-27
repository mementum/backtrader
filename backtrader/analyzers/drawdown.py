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
from backtrader.utils import AutoOrderedDict


__all__ = ['DrawDown', 'TimeDrawDown']


class DrawDown(bt.Analyzer):
    '''计算交易系统 drawdown 统计信息的 analyzer。

    统计内容包括当前 drawdown、金额回撤、最大 drawdown、最大金额回撤、
    当前 drawdown 持续长度和最大持续长度。

    Args:
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 drawdown 基于总净资产 value 还是 fund
            value。将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        AutoOrderedDict: ``get_analysis`` 返回支持 ``.`` 访问的 dict-like
        对象，包含以下 key:

      - ``drawdown``: 当前 drawdown，单位为 0.xx %
      - ``moneydown``: 当前金额回撤
      - ``len``: 当前 drawdown 持续长度
      - ``max.drawdown``: 最大 drawdown，单位为 0.xx %
      - ``max.moneydown``: 最大金额回撤
      - ``max.len``: 最大 drawdown 持续长度

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(DrawDown, _name='drawdown')
    '''

    params = (
        ('fund', None),
    )

    def start(self):
        super(DrawDown, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

    def create_analysis(self):
        self.rets = AutoOrderedDict()  # 支持 . notation 的 dict

        self.rets.len = 0
        self.rets.drawdown = 0.0
        self.rets.moneydown = 0.0

        self.rets.max.len = 0.0
        self.rets.max.drawdown = 0.0
        self.rets.max.moneydown = 0.0

        self._maxvalue = float('-inf')  # 任意 value 都会高于它

    def stop(self):
        self.rets._close()  # . notation 不能再创建更多 key

    def notify_fund(self, cash, value, fundvalue, shares):
        if not self._fundmode:
            self._value = value  # 记录当前 value
            self._maxvalue = max(self._maxvalue, value)  # 更新峰值 value
        else:
            self._value = fundvalue  # 记录当前 value
            self._maxvalue = max(self._maxvalue, fundvalue)  # 更新峰值

    def next(self):
        r = self.rets

        # 计算当前 drawdown 值
        r.moneydown = moneydown = self._maxvalue - self._value
        r.drawdown = drawdown = 100.0 * moneydown / self._maxvalue

        # 最大 drawdown 值
        r.max.moneydown = max(r.max.moneydown, moneydown)
        r.max.drawdown = maxdrawdown = max(r.max.drawdown, drawdown)

        r.len = r.len + 1 if drawdown else 0
        r.max.len = max(r.max.len, r.len)


class TimeDrawDown(bt.TimeFrameAnalyzerBase):
    '''按指定 timeframe 计算交易系统 drawdown 的 analyzer。

    该 timeframe 可以不同于底层 data 使用的 timeframe。

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            使用系统中第 1 个 data 的 timeframe。传入
            ``TimeFrame.NoTimeFrame`` 可在不受时间约束的情况下考虑整个
            dataset。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。如果为 ``None``，使用系统中第 1 个 data 的
            compression。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 drawdown 基于总净资产 value 还是 fund
            value。将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回包含以下 key 的字典:

      - ``maxdrawdown``: 最大 drawdown
      - ``maxdrawdownperiod``: 最大 drawdown 持续 period

    运行过程中也可以直接读取以下属性:

      - ``dd``
      - ``maxdd``
      - ``maxddlen``

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(TimeDrawDown, timeframe=bt.TimeFrame.Months,
    ...                     _name='timedrawdown')
    '''

    params = (
        ('fund', None),
    )

    def start(self):
        super(TimeDrawDown, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund
        self.dd = 0.0
        self.maxdd = 0.0
        self.maxddlen = 0
        self.peak = float('-inf')
        self.ddlen = 0

    def on_dt_over(self):
        if not self._fundmode:
            value = self.strategy.broker.getvalue()
        else:
            value = self.strategy.broker.fundvalue

        # 更新已见到的最大峰值
        if value > self.peak:
            self.peak = value
            self.ddlen = 0  # streak 起点

        # 计算当前 drawdown
        self.dd = dd = 100.0 * (self.peak - value) / self.peak
        self.ddlen += bool(dd)  # 如果 peak == value，则 dd = 0

        # 按需更新 maxdrawdown
        self.maxdd = max(self.maxdd, dd)
        self.maxddlen = max(self.maxddlen, self.ddlen)

    def stop(self):
        self.rets['maxdrawdown'] = self.maxdd
        self.rets['maxdrawdownperiod'] = self.maxddlen
