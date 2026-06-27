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


class DataFilter(bt.AbstractDataBase):
    '''包装 data source，并按 callable 条件过滤 bar 的 data feed。

    除 ``DataBase`` 标准参数外，该类接收 ``funcfilter`` 参数。``funcfilter``
    会以底层 data source 为参数被调用。

    Args:
        funcfilter: 任意 callable。返回 ``True`` 时保留当前 data source bar；
            返回 ``False`` 时丢弃当前 bar。

    Returns:
        bool: ``_load`` 在成功加载一个通过过滤的 bar 时返回 ``True``；底层
        data source 耗尽时返回 ``False``。

    ---
    >>> import backtrader as bt
    >>> def keep_positive_close(data):
    ...     return data.close[0] > 0
    >>> data = bt.feeds.GenericCSVData(dataname='prices.csv')
    >>> filtered = DataFilter(dataname=data, funcfilter=keep_positive_close)
    '''
    params = (('funcfilter', None),)

    def preload(self):
        if len(self.p.dataname) == self.p.dataname.buflen():
            # 如果 data 尚未 preload，则执行 preload
            self.p.dataname.start()
            self.p.dataname.preload()
            self.p.dataname.home()

        # start 后从 data 复制 timeframe（部分 source 会自动检测）
        self.p.timeframe = self._timeframe = self.p.dataname._timeframe
        self.p.compression = self._compression = self.p.dataname._compression

        super(DataFilter, self).preload()

    def _load(self):
        if not len(self.p.dataname):
            self.p.dataname.start()  # 如果其他地方尚未 start data，则 start

        # 通知底层 source 获取下一条 data
        while self.p.dataname.next():
            # 尝试从底层 source 加载 data
            if not self.p.funcfilter(self.p.dataname):
                continue

            # data 被允许通过，复制 line 数量对应的数据
            for i in range(self.p.dataname.size()):
                self.lines[i][0] = self.p.dataname.lines[i][0]

            return True

        return False  # 底层 source 没有更多 data
