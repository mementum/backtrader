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


import collections

import backtrader as bt
from backtrader import Order, Position


class Transactions(bt.Analyzer):
    '''报告系统中每个 data 发生的 transaction。

    该 analyzer 会读取 order execution bits，并在每个 ``next`` cycle 中从 0
    开始构造临时 ``Position``，用来汇总该 cycle 内发生的 transaction。

    Args:
        headers (bool): 是否在结果字典中添加初始 header，默认 ``False``。
        _pfheaders (tuple): pyfolio 风格的 header 名称，默认包含
            ``date``、``amount``、``price``、``sid``、``symbol``、``value``。

    Returns:
        dict: ``get_analysis`` 返回以 datetime 为 key、transaction 列表为
        value 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(Transactions, headers=True, _name='transactions')
    '''
    params = (
        ('headers', False),
        ('_pfheaders', ('date', 'amount', 'price', 'sid', 'symbol', 'value')),
    )

    def start(self):
        super(Transactions, self).start()
        if self.p.headers:
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]

        self._positions = collections.defaultdict(Position)
        self._idnames = list(enumerate(self.strategy.getdatanames()))

    def notify_order(self, order):
        # 一个 order 在单个 cycle 中可能有多次 partial execution（少见但可能）
        # 因此先收集每个新的 execution notification，把汇总留给 next

        # 每轮使用新的 Position 对象，汇总本轮 execution bits 的效果
        if order.status not in [Order.Partial, Order.Completed]:
            return  # 不是 execution

        pos = self._positions[order.data._name]
        for exbit in order.executed.iterpending():
            if exbit is None:
                break  # 已到达 pending 末尾

            pos.update(exbit.size, exbit.price)

    def next(self):
        # super(Transactions, self).next()  # 让 dtkey 更新
        entries = []
        for i, dname in self._idnames:
            pos = self._positions.get(dname, None)
            if pos is not None:
                size, price = pos.size, pos.price
                if size:
                    entries.append([size, price, i, dname, -size * price])

        if entries:
            self.rets[self.strategy.datetime.datetime()] = entries

        self._positions.clear()
