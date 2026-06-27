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


class PositionsValue(bt.Analyzer):
    '''报告当前所有 data position value 的 analyzer。

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            使用系统中第 1 个 data 的 timeframe。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。如果为 ``None``，使用系统中第 1 个 data 的
            compression。
        headers (bool): 是否在结果字典中添加一条初始 header，默认
            ``False``。header 使用 data 名称，key 为 ``Datetime``。
        cash (bool): 是否把当前 cash 作为额外 position 加入结果，默认
            ``False``。启用 header 时该列名为 ``cash``。

    Returns:
        dict: ``get_analysis`` 返回以 date/datetime 为 key、各 data position
        value 列表为 value 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(PositionsValue, headers=True, cash=True,
    ...                     _name='positions')
    '''
    params = (
        ('headers',  False),
        ('cash', False),
    )

    def start(self):
        if self.p.headers:
            headers = [d._name or 'Data%d' % i
                       for i, d in enumerate(self.datas)]
            self.rets['Datetime'] = headers + ['cash'] * self.p.cash

        tf = min(d._timeframe for d in self.datas)
        self._usedate = tf >= bt.TimeFrame.Days

    def next(self):
        pvals = [self.strategy.broker.get_value([d]) for d in self.datas]
        if self.p.cash:
            pvals.append(self.strategy.broker.get_cash())

        if self._usedate:
            self.rets[self.strategy.datetime.date()] = pvals
        else:
            self.rets[self.strategy.datetime.datetime()] = pvals
