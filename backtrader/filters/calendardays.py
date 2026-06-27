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

from datetime import date, datetime, timedelta

from backtrader import TimeFrame
from backtrader.utils.py3 import with_metaclass
from .. import metabase


class CalendarDays(with_metaclass(metabase.MetaParams, object)):
    '''为交易日之间缺失的自然日补 bar 的 Bar Filler。

    Args:
        fill_price: 缺失 bar 使用的价格，默认 ``None``。
            大于 0 时使用给定值；为 0 或 ``None`` 时使用上一根已知 close；
            为 ``-1`` 时使用上一根 bar 的 midpoint（High-Low average）。
        fill_vol: 缺失 bar 使用的 volume，默认 ``NaN``。
        fill_oi: 缺失 bar 使用的 open interest，默认 ``NaN``。

    Returns:
        None: filter 会把补出的 bar 加入 data stack。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='daily.csv')
    >>> data.addfilter(CalendarDays, fill_price=None)
    '''
    params = (('fill_price', None),
              ('fill_vol', float('NaN')),
              ('fill_oi', float('NaN')),)

    ONEDAY = timedelta(days=1)
    lastdt = date.max

    def __init__(self, data):
        pass

    def __call__(self, data):
        '''处理一根 data bar，并在自然日 gap 大于 1 天时补 bar。

        Args:
            data: 要过滤/处理的 data source。

        Returns:
            bool: 始终返回 ``False``，表示该 filter 不从 stream 中移除 bar。

        '''
        dt = data.datetime.date()
        if (dt - self.lastdt) > self.ONEDAY:  # 存在 gap
            self._fillbars(data, dt, self.lastdt)

        self.lastdt = dt
        return False  # 未从 stream 中移除 bar

    def _fillbars(self, data, dt, lastdt):
        '''按需逐根填补从 ``lastdt`` 到 ``dt`` 之间的 bar。

        Args:
            data: 要补 bar 的 data source。
            dt: 当前 bar 的日期。
            lastdt: 上一根 bar 的日期。

        Returns:
            None: 补出的 bar 会加入 data stack。
        '''
        tm = data.datetime.time(0)  # 获取 time 部分

        # 所有补 bar 使用同一价格
        if self.p.fill_price > 0:
            price = self.p.fill_price
        elif not self.p.fill_price:
            price = data.close[-1]
        elif self.p.fill_price == -1:
            price = (data.high[-1] + data.low[-1]) / 2.0

        while lastdt < dt:
            lastdt += self.ONEDAY

            # 准备所需大小的数组
            bar = [float('Nan')] * data.size()
            # 填充 datetime
            bar[data.DateTime] = data.date2num(datetime.combine(lastdt, tm))

            # 填充 price 字段
            for pricetype in [data.Open, data.High, data.Low, data.Close]:
                bar[pricetype] = price

            # 填充 volume 和 open interest
            bar[data.Volume] = self.p.fill_vol
            bar[data.OpenInterest] = self.p.fill_oi

            # 填充 data feed 可能在 DateTime 之后定义的额外 lines
            for i in range(data.DateTime + 1, data.size()):
                bar[i] = data.lines[i][0]

            # 将构造出的 bar 加入 stream stack
            data._add2stack(bar)

        # 将触发 gap 的 bar 保存到 stack
        data._save2stack(erase=True)
