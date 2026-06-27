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

from collections import OrderedDict

from backtrader.utils.py3 import range
from backtrader import Analyzer


class AnnualReturn(Analyzer):
    '''按自然年计算年度收益率的 analyzer。

    该 analyzer 会比较每一年的起始 value 和结束 value，生成年度 return。

    Args:
        无。

    Returns:
        OrderedDict: ``get_analysis`` 返回以年份为 key、年度 return 为 value
        的字典。

    Member Attributes:
        rets (list): 已计算的年度 return 列表。
        ret (OrderedDict): 以年份为 key 的年度 return 字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(AnnualReturn, _name='annual')
    '''

    def stop(self):
        # 必须有 stats.broker
        cur_year = -1

        value_start = 0.0
        value_cur = 0.0
        value_end = 0.0

        self.rets = list()
        self.ret = OrderedDict()

        for i in range(len(self.data) - 1, -1, -1):
            dt = self.data.datetime.date(-i)
            value_cur = self.strategy.stats.broker.value[-i]

            if dt.year > cur_year:
                if cur_year >= 0:
                    annualret = (value_end / value_start) - 1.0
                    self.rets.append(annualret)
                    self.ret[cur_year] = annualret

                    # 跨自然年时，使用上一年最后 value 作为新的起点
                    value_start = value_end
                else:
                    # 尚未设置任何 value，使用当前已加载 value
                    value_start = value_cur

                cur_year = dt.year

            # 无论如何，最后 value 始终是最后加载到的 value
            value_end = value_cur

        if cur_year not in self.ret:
            # 完成待处理数据的计算
            annualret = (value_end / value_start) - 1.0
            self.rets.append(annualret)
            self.ret[cur_year] = annualret

    def get_analysis(self):
        return self.ret
