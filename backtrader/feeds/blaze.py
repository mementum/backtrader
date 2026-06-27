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

from backtrader import date2num
import backtrader.feed as feed


class BlazeData(feed.DataBase):
    '''
    支持 `Blaze <blaze.pydata.org>`_ 的 ``Data`` 对象。

    这里只支持使用数字索引定位列。

    Args:
        dataname: Blaze ``Data`` 对象。
        datetime: datetime 字段的数字列索引，必须存在。
        open: open 字段的数字列索引，传入负数表示不存在。
        high: high 字段的数字列索引，传入负数表示不存在。
        low: low 字段的数字列索引，传入负数表示不存在。
        close: close 字段的数字列索引，传入负数表示不存在。
        volume: volume 字段的数字列索引，传入负数表示不存在。
        openinterest: openinterest 字段的数字列索引，传入负数表示不存在。

    Returns:
        BlazeData: 可加入 Cerebro 的 Blaze 数据源实例。

    ---
    交互界面使用示范:

    >>> data = BlazeData(dataname=[])
    >>> data.p.datetime
    0
    '''

    params = (
        # datetime 必须存在
        ('datetime', 0),
        # 下列字段传 -1 表示不存在
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', 6),
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]

    def start(self):
        super(BlazeData, self).start()

        # 每次 start 时重置迭代器
        self._rows = iter(self.p.dataname)

    def _load(self):
        try:
            row = next(self._rows)
        except StopIteration:
            return False

        # 设置标准 datafield，datetime 单独处理
        for datafield in self.datafields[1:]:
            # 获取字段所在的列索引
            colidx = getattr(self.params, datafield)

            if colidx < 0:
                # 数据源中没有该列，跳过
                continue

            # 获取要写入的 line
            line = getattr(self.lines, datafield)
            line[0] = row[colidx]

        # datetime：假定 blaze 总是提供原生 datetime.datetime
        colidx = getattr(self.params, self.datafields[0])
        dt = row[colidx]
        dtnum = date2num(dt)

        # 获取要写入的 line
        line = getattr(self.lines, self.datafields[0])
        line[0] = dtnum

        # 当前 bar 加载完成
        return True
