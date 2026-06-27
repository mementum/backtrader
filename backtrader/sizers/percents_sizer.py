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

__all__ = ['PercentSizer', 'AllInSizer', 'PercentSizerInt', 'AllInSizerInt']


class PercentSizer(bt.Sizer):
    '''按可用 cash 的百分比返回 size 的 sizer。

    如果当前 data 没有持仓，则用 ``cash / data.close[0] * percents / 100``
    计算 size；如果已经有持仓，则返回当前 position size。

    Args:
        percents (float): 使用可用 cash 的百分比，默认 ``20``。
        retint (bool): 是否把返回 size 截断为 int，默认 ``False``。

    Returns:
        float | int: 计算得到的 size；``retint`` 为 ``True`` 时返回 int。

    ---
    >>> class Broker:
    ...     def getposition(self, data):
    ...         return 0
    >>> class Close:
    ...     def __getitem__(self, ago):
    ...         return 10.0
    >>> class Data:
    ...     close = Close()
    >>> sizer = PercentSizer(percents=25)
    >>> sizer.broker = Broker()
    >>> sizer._getsizing(None, 1000.0, Data(), True)
    25.0
    '''

    params = (
        ('percents', 20),
        ('retint', False),  # 返回 int size，还是保留 float value
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = position.size

        if self.p.retint:
            size = int(size)

        return size


class AllInSizer(PercentSizer):
    '''使用 broker 全部可用 cash 计算 size 的 sizer。

    Args:
        percents (float): 使用可用 cash 的百分比，默认 ``100``。

    Returns:
        float: 计算得到的全仓 size。

    ---
    >>> sizer = AllInSizer()
    >>> sizer.p.percents
    100
     '''
    params = (
        ('percents', 100),
    )


class PercentSizerInt(PercentSizer):
    '''按可用 cash 的百分比返回 size，并将结果截断为 int 的 sizer。

    Args:
        percents (float): 使用可用 cash 的百分比，默认 ``20``。

    Returns:
        int: 截断为 int 的 size。

    ---
    >>> sizer = PercentSizerInt()
    >>> sizer.p.retint
    True
    '''

    params = (
        ('retint', True),  # 返回 int size，还是保留 float value
    )


class AllInSizerInt(PercentSizerInt):
    '''使用 broker 全部可用 cash 计算 size，并将结果截断为 int 的 sizer。

    Args:
        percents (float): 使用可用 cash 的百分比，默认 ``100``。

    Returns:
        int: 截断为 int 的全仓 size。

    ---
    >>> sizer = AllInSizerInt()
    >>> sizer.p.percents, sizer.p.retint
    (100, True)
     '''
    params = (
        ('percents', 100),
    )
