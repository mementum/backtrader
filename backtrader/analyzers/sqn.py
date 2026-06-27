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

from backtrader import Analyzer
from backtrader.mathsupport import average, standarddev
from backtrader.utils import AutoOrderedDict


class SQN(Analyzer):
    '''计算 SQN（System Quality Number）的 analyzer。

    SQN 由 Van K. Tharp 定义，用于给交易系统分类。

      - 1.6 - 1.9 Below average
      - 2.0 - 2.4 Average
      - 2.5 - 2.9 Good
      - 3.0 - 5.0 Excellent
      - 5.1 - 6.9 Superb
      - 7.0 -     Holy Grail?

    公式:

      - SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit)

    当 trade 数量 >= 30 时，SQN 值通常更可靠。

    Args:
        无。

    Returns:
        AutoOrderedDict: ``get_analysis`` 返回包含以下 key 的对象:

      - ``sqn``: 计算得到的 SQN
      - ``trades``: 纳入计算的 trade 数量

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(SQN, _name='sqn')

    '''
    alias = ('SystemQualityNumber',)

    def create_analysis(self):
        '''使用 ``AutoOrderedDict`` 替代默认 ``OrderedDict``。

        Returns:
            None: 该方法只初始化 ``self.rets``。
        '''
        self.rets = AutoOrderedDict()

    def start(self):
        super(SQN, self).start()
        self.pnl = list()
        self.count = 0

    def notify_trade(self, trade):
        if trade.status == trade.Closed:
            self.pnl.append(trade.pnlcomm)
            self.count += 1

    def stop(self):
        if self.count > 1:
            pnl_av = average(self.pnl)
            pnl_stddev = standarddev(self.pnl)
            try:
                sqn = math.sqrt(len(self.pnl)) * pnl_av / pnl_stddev
            except ZeroDivisionError:
                sqn = None
        else:
            sqn = 0

        self.rets.sqn = sqn
        self.rets.trades = self.count
