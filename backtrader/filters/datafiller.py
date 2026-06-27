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
from datetime import datetime, timedelta

from backtrader import AbstractDataBase, TimeFrame


class DataFiller(AbstractDataBase):
    '''根据底层 data source 信息填补缺失 bar 的 data feed。

    填补逻辑会使用底层 data source 的 timeframe、compression、sessionstart
    和 sessionend 来确定输出 bar 的时间间隔。

    例如分钟级 data 在 10:31 和 10:34 之间缺少 bar，本类会用上一根 bar
    （10:31）的 close 价格补出 10:32 和 10:33。

    Args:
        fill_price: 缺失 bar 使用的价格，默认 ``None``。如果为 ``None`` 或
            求值为 ``False``，使用上一根 bar 的 close；否则使用传入值，例如
            ``float('NaN')``。
        fill_vol: 缺失 bar 使用的 volume，默认 ``NaN``。
        fill_oi: 缺失 bar 使用的 openinterest，默认 ``NaN``。

    Returns:
        bool: ``_load`` 在输出原始或补出的 bar 时返回 ``True``；底层数据耗尽
        时返回 ``False``。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='intraday.csv')
    >>> filled = DataFiller(dataname=data, fill_vol=0.0)
    '''

    params = (
        ('fill_price', None),
        ('fill_vol', float('NaN')),
        ('fill_oi', float('NaN')),
        )

    def start(self):
        super(DataFiller, self).start()
        self._fillbars = collections.deque()
        self._dbar = False

    def preload(self):
        if len(self.p.dataname) == self.p.dataname.buflen():
            # 如果 data 尚未 preload，则执行 preload
            self.p.dataname.start()
            self.p.dataname.preload()
            self.p.dataname.home()

        # start 后从 data 复制 timeframe（部分 source 会自动检测）
        self.p.timeframe = self._timeframe = self.p.dataname._timeframe
        self.p.compression = self._compression = self.p.dataname._compression

        super(DataFiller, self).preload()

    def _copyfromdata(self):
        # data 被允许通过，复制 line 数量对应的数据
        for i in range(self.p.dataname.size()):
            self.lines[i][0] = self.p.dataname.lines[i][0]

        self._dbar = False  # 使已读取 bar 的标记失效

        return True

    def _frombars(self):
        dtime, price = self._fillbars.popleft()

        price = self.p.fill_price or price

        self.lines.datetime[0] = self.p.dataname.date2num(dtime)
        self.lines.open[0] = price
        self.lines.high[0] = price
        self.lines.low[0] = price
        self.lines.close[0] = price
        self.lines.volume[0] = self.p.fill_vol
        self.lines.openinterest[0] = self.p.fill_oi

        return True

    # bar 之间的最小 delta 单位
    _tdeltas = {
        TimeFrame.Minutes: timedelta(seconds=60),
        TimeFrame.Seconds: timedelta(seconds=1),
        TimeFrame.MicroSeconds: timedelta(microseconds=1),
    }

    def _load(self):
        if not len(self.p.dataname):
            self.p.dataname.start()  # 如果其他地方尚未 start data，则 start

            # 从底层 data 复制
            self._timeframe = self.p.dataname._timeframe
            self._compression = self.p.dataname._compression

            self.p.timeframe = self._timeframe
            self.p.compression = self._compression

            # 计算并保存 timeframe 对应的 timedelta
            self._tdunit = self._tdeltas[self._timeframe]
            self._tdunit *= self._compression

        if self._fillbars:
            return self._frombars()

        # 使用现有 bar 或获取新 bar
        self._dbar = self._dbar or self.p.dataname.next()
        if not self._dbar:
            return False  # 没有更多 data

        if len(self) == 1:
            # 还不能向后查看，按原样输出 data
            return self._copyfromdata()

        # 上一根已输出 bar 的 close
        pclose = self.lines.close[-1]
        # 获取上一根已输出 bar 的时间
        dtime_prev = self.lines.datetime.datetime(-1)
        # 获取当前底层 data source bar 的时间
        dtime_cur = self.p.dataname.datetime.datetime(0)

        # 计算上一根 bar 所在 session 的结束时间
        send = datetime.combine(dtime_prev.date(), self.p.dataname.sessionend)

        if dtime_cur > send:  # 如果跨过 session 边界
            # 1. 检查到 session 结束前是否缺 bar
            dtime_prev += self._tdunit
            while dtime_prev < send:
                self._fillbars.append((dtime_prev, pclose))
                dtime_prev += self._tdunit

            # 计算新 bar 所在 session 的开始时间
            sstart = datetime.combine(
                dtime_cur.date(), self.p.dataname.sessionstart)

            # 2. 检查从新 session 起点到当前 bar 前是否缺 bar
            while sstart < dtime_cur:
                self._fillbars.append((sstart, pclose))
                sstart += self._tdunit
        else:
            # 未跨边界，检查到当前时间前的 gap
            dtime_prev += self._tdunit
            while dtime_prev < dtime_cur:
                self._fillbars.append((dtime_prev, pclose))
                dtime_prev += self._tdunit

        if self._fillbars:
            self._dbar = True  # 标记有一个 pending data bar 可用

            # 在当前 cycle 返回一根累积出来的 bar
            return self._frombars()

        return self._copyfromdata()
