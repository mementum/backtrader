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


from backtrader.utils.py3 import MAXINT, with_metaclass

from backtrader.metabase import MetaParams


class FixedSize(with_metaclass(MetaParams, object)):
    '''按固定上限返回给定 order 的 execution size。

    Args:
        size: 最大可执行 size。实际执行时的 bar volume 也是限制；如果 bar
            volume 更小，则使用更小值。

    如果该参数的值为 False，则使用 bar 的全部 volume 来匹配 order。

    ---
    交互示例:

    >>> class Line:
    ...     def __getitem__(self, ago):
    ...         return 100
    >>> class Data:
    ...     volume = Line()
    >>> class Executed:
    ...     remsize = 25
    >>> class Order:
    ...     data = Data()
    ...     executed = Executed()
    >>> FixedSize(size=10)(Order(), price=100.0, ago=0)
    10
    '''
    params = (('size', None),)

    def __call__(self, order, price, ago):
        '''计算可执行 size。

        Args:
            order: 当前 order，需提供 ``data.volume`` 和 ``executed.remsize``。
            price (float): 当前 execution price。
            ago (int): 访问 data line 时使用的相对位置。

        Returns:
            int: 当前可执行 size。
        '''
        size = self.p.size or MAXINT
        return min((order.data.volume[ago], abs(order.executed.remsize), size))


class FixedBarPerc(with_metaclass(MetaParams, object)):
    '''使用 bar volume 的固定百分比返回给定 order 的 execution size。

    Args:
        perc (float): 用于执行 order 的 bar volume 百分比，合法值为
            ``0.0 - 100.0``。

    ---
    交互示例:

    >>> class Line:
    ...     def __getitem__(self, ago):
    ...         return 100
    >>> class Data:
    ...     volume = Line()
    >>> class Executed:
    ...     remsize = 80
    >>> class Order:
    ...     data = Data()
    ...     executed = Executed()
    >>> FixedBarPerc(perc=50.0)(Order(), price=100.0, ago=0)
    50.0
    '''
    params = (('perc', 100.0),)

    def __call__(self, order, price, ago):
        '''计算按 bar volume 百分比限制后的可执行 size。

        Args:
            order: 当前 order，需提供 ``data.volume`` 和 ``executed.remsize``。
            price (float): 当前 execution price。
            ago (int): 访问 data line 时使用的相对位置。

        Returns:
            float: 当前可执行 size。
        '''
        # 获取 volume，并按请求的 perc 缩放
        maxsize = (order.data.volume[ago] * self.p.perc) // 100
        # 返回最大可能执行 volume
        return min(maxsize, abs(order.executed.remsize))


class BarPointPerc(with_metaclass(MetaParams, object)):
    '''返回给定 order 的 execution size，并按 price 区间分配 bar volume。

    volume 会在 *high*-*low* 区间内用 ``minmov`` 分区并均匀分布。给定 price
    分到的 volume 会再按 ``perc`` 百分比用于匹配。

    Args:
        minmov (float): 最小 price movement。用于将 *high*-*low* 区间分区，
            以便在可能 price 之间按比例分配 volume。
        perc (float): 分配给 order execution price 的 volume 中用于匹配的
            百分比，合法值为 ``0.0 - 100.0``。

    ---
    交互示例:

    >>> class Line:
    ...     def __init__(self, value):
    ...         self.value = value
    ...     def __getitem__(self, ago):
    ...         return self.value
    >>> class Data:
    ...     high = Line(101.0)
    ...     low = Line(100.0)
    ...     volume = Line(100)
    >>> class Executed:
    ...     remsize = 80
    >>> class Order:
    ...     data = Data()
    ...     executed = Executed()
    >>> BarPointPerc(minmov=0.5, perc=50.0)(Order(), price=100.5, ago=0)
    16.0
    '''
    params = (
        ('minmov', None),
        ('perc', 100.0),
    )

    def __call__(self, order, price, ago):
        '''计算按 price 分区和百分比限制后的可执行 size。

        Args:
            order: 当前 order，需提供 ``data.high``、``data.low``、
                ``data.volume`` 和 ``executed.remsize``。
            price (float): 当前 execution price。
            ago (int): 访问 data line 时使用的相对位置。

        Returns:
            float: 当前可执行 size。
        '''
        data = order.data
        minmov = self.p.minmov

        parts = 1
        if minmov:
            # high - low + minmov 用于处理开区间减法
            parts = (data.high[ago] - data.low[ago] + minmov) // minmov

        alloc_vol = ((data.volume[ago] / parts) * self.p.perc) // 100.0

        # 返回最大可能执行 volume
        return min(alloc_vol, abs(order.executed.remsize))
