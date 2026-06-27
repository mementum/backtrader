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

from datetime import datetime
import itertools

from .. import feed, TimeFrame
from ..utils import date2num
from ..utils.py3 import integer_types, string_types


class GenericCSVData(feed.CSVDataBase):
    '''按参数定义的字段顺序和字段存在性解析 CSV 文件的 data feed。

    Args:
        dataname: 要解析的文件名或 file-like 对象。
        datetime (int): datetime 字段所在列索引，默认 ``0``。
        time (int): time 字段所在列索引，默认 ``-1``，表示不存在独立 time
            字段。如果 ``time >= 0``，date 和 time 会被合并。
        open (int): open 字段所在列索引，默认 ``1``。
        high (int): high 字段所在列索引，默认 ``2``。
        low (int): low 字段所在列索引，默认 ``3``。
        close (int): close 字段所在列索引，默认 ``4``。
        volume (int): volume 字段所在列索引，默认 ``5``。
        openinterest (int): openinterest 字段所在列索引，默认 ``6``。
        nullvalue: CSV 字段缺失或为空时使用的值，默认 ``NaN``。
        dtformat: 解析 datetime CSV 字段使用的格式，默认
            ``'%Y-%m-%d %H:%M:%S'``。可传入:

          - ``1``: Unix timestamp，``int`` 秒数，自 1970-01-01 起算
          - ``2``: Unix timestamp，``float`` 秒数
          - callable: 接收字符串并返回 ``datetime.datetime`` 实例

        tmformat: 独立 time CSV 字段存在时使用的解析格式，默认 ``'%H:%M:%S'``。

    Returns:
        bool: ``_loadline`` 成功解析一行时返回 ``True``。

    ---
    >>> data = GenericCSVData(dataname='prices.csv', dtformat='%Y-%m-%d')

    '''

    params = (
        ('nullvalue', float('NaN')),
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('tmformat', '%H:%M:%S'),

        ('datetime', 0),
        ('time', -1),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', 6),
    )

    def start(self):
        super(GenericCSVData, self).start()

        self._dtstr = False
        if isinstance(self.p.dtformat, string_types):
            self._dtstr = True
        elif isinstance(self.p.dtformat, integer_types):
            idt = int(self.p.dtformat)
            if idt == 1:
                self._dtconvert = lambda x: datetime.utcfromtimestamp(int(x))
            elif idt == 2:
                self._dtconvert = lambda x: datetime.utcfromtimestamp(float(x))

        else:  # 假定为 callable
            self._dtconvert = self.p.dtformat

    def _loadline(self, linetokens):
        # Datetime 需要特殊处理
        dtfield = linetokens[self.p.datetime]
        if self._dtstr:
            dtformat = self.p.dtformat

            if self.p.time >= 0:
                # 如果 time 位于独立字段，则追加 time 值和格式
                dtfield += 'T' + linetokens[self.p.time]
                dtformat += 'T' + self.p.tmformat

            dt = datetime.strptime(dtfield, dtformat)
        else:
            dt = self._dtconvert(dtfield)

        if self.p.timeframe >= TimeFrame.Days:
            # 检查预期 session end 是否大于解析出的时间
            if self._tzinput:
                dtin = self._tzinput.localize(dt)  # pytz 兼容化
            else:
                dtin = dt

            dtnum = date2num(dtin)  # 转为 UTC

            dteos = datetime.combine(dt.date(), self.p.sessionend)
            dteosnum = self.date2num(dteos)  # 转为 UTC

            if dteosnum > dtnum:
                self.lines.datetime[0] = dteosnum
            else:
                # 如果已经转换且 dtin == dt，避免重复转换
                self.l.datetime[0] = date2num(dt) if self._tzinput else dtnum
        else:
            self.lines.datetime[0] = date2num(dt)

        # 其余字段可用相同流程处理
        for linefield in (x for x in self.getlinealiases() if x != 'datetime'):
            # 获取由传入 params 创建的索引
            csvidx = getattr(self.params, linefield)

            if csvidx is None or csvidx < 0:
                # 字段不存在，赋值为 nullvalue
                csvfield = self.p.nullvalue
            else:
                # 从 token 获取字段
                csvfield = linetokens[csvidx]

            if csvfield == '':
                # 如果为空，赋值为 nullvalue
                csvfield = self.p.nullvalue

            # 获取对应 line 引用并设置 value
            line = getattr(self.lines, linefield)
            line[0] = float(float(csvfield))

        return True


class GenericCSV(feed.CSVFeedBase):
    DataCls = GenericCSVData
