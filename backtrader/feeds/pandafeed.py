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

from backtrader.utils.py3 import filter, string_types, integer_types

from backtrader import date2num
import backtrader.feed as feed


class PandasDirectData(feed.DataBase):
    '''
    使用 Pandas DataFrame 作为数据源，直接遍历 ``itertuples`` 返回的 tuple。

    因为直接读取 tuple，所有 line 相关参数都必须使用数字索引。

    Args:
        dataname: Pandas DataFrame。
        datetime: datetime 字段在 tuple 中的索引。
        open: open 字段在 tuple 中的索引。
        high: high 字段在 tuple 中的索引。
        low: low 字段在 tuple 中的索引。
        close: close 字段在 tuple 中的索引。
        volume: volume 字段在 tuple 中的索引。
        openinterest: openinterest 字段在 tuple 中的索引。任一 data line 参数为负数时，
            表示 DataFrame 中不存在对应字段。

    Returns:
        PandasDirectData: 可加入 Cerebro 的 Pandas 直读数据源实例。

    ---
    交互界面使用示范:

    >>> class Frame:
    ...     def itertuples(self):
    ...         return iter(())
    >>> data = PandasDirectData(dataname=Frame())
    >>> data.p.open
    1
    '''

    params = (
        ('datetime', 0),
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
        super(PandasDirectData, self).start()

        # 每次 start 时重置迭代器
        self._rows = self.p.dataname.itertuples()

    def _load(self):
        try:
            row = next(self._rows)
        except StopIteration:
            return False

        # 设置标准 datafield，datetime 单独处理
        for datafield in self.getlinealiases():
            if datafield == 'datetime':
                continue

            # 读取字段所在的列索引
            colidx = getattr(self.params, datafield)

            if colidx < 0:
                # DataFrame 中没有该列，跳过
                continue

            # 获取要写入的 line
            line = getattr(self.lines, datafield)

            # Pandas tuple 索引：直接按列位置取值
            line[0] = row[colidx]

        # 处理 datetime 字段
        colidx = getattr(self.params, 'datetime')
        tstamp = row[colidx]

        # 通过 datetime 转成浮点日期并存储
        dt = tstamp.to_pydatetime()
        dtnum = date2num(dt)

        # 获取要写入的 line
        line = getattr(self.lines, 'datetime')
        line[0] = dtnum

        # 当前 bar 加载完成
        return True


class PandasData(feed.DataBase):
    '''
    使用 Pandas DataFrame 作为数据源，通过列名或列索引映射到各个 line。

    Args:
        dataname: Pandas DataFrame。
        nocase: 是否对列名进行大小写不敏感匹配，默认 ``True``。
        datetime: datetime 字段来源。``None`` 表示 DataFrame index 保存 datetime；
            ``-1`` 表示自动检测列名；非负整数或字符串表示明确的列索引/列名。
        open: open 字段来源。``None`` 表示不存在，``-1`` 表示自动检测，非负整数或
            字符串表示明确的列索引/列名。
        high: high 字段来源，含义同 ``open``。
        low: low 字段来源，含义同 ``open``。
        close: close 字段来源，含义同 ``open``。
        volume: volume 字段来源，含义同 ``open``。
        openinterest: openinterest 字段来源，含义同 ``open``。

    Returns:
        PandasData: 可加入 Cerebro 的 Pandas 数据源实例。

    ---
    交互界面使用示范:

    >>> class Columns:
    ...     values = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    >>> class Frame:
    ...     columns = Columns()
    >>> data = PandasData(dataname=Frame())
    >>> data._colmapping['open']
    'open'
    '''

    params = (
        ('nocase', True),

        # datetime 的可选值（必须能找到）
        #  None : datetime 存在于 Pandas DataFrame 的 index 中
        #  -1 : 自动检测位置或大小写匹配的同名列
        #  >= 0 : Pandas DataFrame 中的数字列索引
        #  string : Pandas DataFrame 中的列名
        ('datetime', None),

        # 下列字段的可选值：
        #  None : 不存在对应列
        #  -1 : 自动检测位置或大小写匹配的同名列
        #  >= 0 : Pandas DataFrame 中的数字列索引
        #  string : Pandas DataFrame 中的列名
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]

    def __init__(self):
        super(PandasData, self).__init__()

        # colnames 可以是字符串，也可以是数字类型
        colnames = list(self.p.dataname.columns.values)
        if self.p.datetime is None:
            # datetime 预期在 index 中，因此不会出现在 columns 中
            pass

        # 尝试判断所有列名是否都是数字
        cstrings = filter(lambda x: isinstance(x, string_types), colnames)
        colsnumeric = not len(list(cstrings))

        # 每个 datafield 对应到哪个列
        self._colmapping = dict()

        # 提前构建外部列到内部 line 的映射
        for datafield in self.getlinealiases():
            defmapping = getattr(self.params, datafield)

            if isinstance(defmapping, integer_types) and defmapping < 0:
                # 请求自动检测
                for colname in colnames:
                    if isinstance(colname, string_types):
                        if self.p.nocase:
                            found = datafield.lower() == colname.lower()
                        else:
                            found = datafield == colname

                        if found:
                            self._colmapping[datafield] = colname
                            break

                if datafield not in self._colmapping:
                    # 请求自动检测但没有找到对应列
                    self._colmapping[datafield] = None
                    continue
            else:
                # 其他情况直接使用给定索引或列名
                self._colmapping[datafield] = defmapping

    def start(self):
        super(PandasData, self).start()

        # 每次 start 时重置行位置
        self._idx = -1

        # 把列名转换为适合 .iloc 使用的列索引
        if self.p.nocase:
            colnames = [x.lower() for x in self.p.dataname.columns.values]
        else:
            colnames = [x for x in self.p.dataname.columns.values]

        for k, v in self._colmapping.items():
            if v is None:
                continue  # datetime 或缺失字段的特殊标记
            if isinstance(v, string_types):
                try:
                    if self.p.nocase:
                        v = colnames.index(v.lower())
                    else:
                        v = colnames.index(v)
                except ValueError as e:
                    defmap = getattr(self.params, k)
                    if isinstance(defmap, integer_types) and defmap < 0:
                        v = None
                    else:
                        raise e  # 让用户看到具体失败原因

            self._colmapping[k] = v

    def _load(self):
        self._idx += 1

        if self._idx >= len(self.p.dataname):
            # 所有行已经读完
            return False

        # 设置标准 datafield
        for datafield in self.getlinealiases():
            if datafield == 'datetime':
                continue

            colindex = self._colmapping[datafield]
            if colindex is None:
                # 数据流中没有该 datafield，跳过
                continue

            # 获取要写入的 line
            line = getattr(self.lines, datafield)

            # Pandas iloc 索引：先行后列
            line[0] = self.p.dataname.iloc[self._idx, colindex]

        # 转换 datetime
        coldtime = self._colmapping['datetime']

        if coldtime is None:
            # datetime 使用标准 index
            tstamp = self.p.dataname.index[self._idx]
        else:
            # datetime 在普通列中，使用对应列索引
            tstamp = self.p.dataname.iloc[self._idx, coldtime]

        # 通过 datetime 转成浮点日期并存储
        dt = tstamp.to_pydatetime()
        dtnum = date2num(dt)
        self.lines.datetime[0] = dtnum

        # 当前 bar 加载完成
        return True
