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


class GrossLeverage(bt.Analyzer):
    '''按时间点计算当前 strategy 的 Gross Leverage。

    Args:
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 leverage 基于总净资产 value 还是 fund
            value。将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回以 datetime 为 key、Gross Leverage 为
        value 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(GrossLeverage, _name='grossleverage')
    '''

    params = (
        ('fund', None),
    )

    def start(self):
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

    def notify_fund(self, cash, value, fundvalue, shares):
        self._cash = cash
        if not self._fundmode:
            self._value = value
        else:
            self._value = fundvalue

    def next(self):
        # 每个 cycle 更新 leverage
        # 100% cash 时为 0.0；无 short selling 且满仓时为 1.0
        lev = (self._value - self._cash) / self._value
        self.rets[self.data0.datetime.datetime()] = lev
