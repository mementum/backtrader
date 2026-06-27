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

import datetime

import backtrader as bt


class DaySplitter_Close(bt.with_metaclass(bt.MetaParams, object)):
    '''将日线 bar 拆成两部分，用两个 tick 模拟 replay data 的 filter。

    拆分结果:

      - 第 1 个 tick: ``OHLX``

        ``Close`` 会被替换为 ``Open``、``High`` 和 ``Low`` 的平均值，并使用
        session opening time。

      - 第 2 个 tick: ``CCCC``

        使用 ``Close`` 价格填充四个 price 组件，并使用 session closing time。

    Args:
        closevol (float): 分配给 closing tick 的 volume 比例，默认 ``0.5``。
            取值按 0.0 到 1.0 的绝对比例理解，剩余 volume 分配给 ``OHLX`` tick。

    Returns:
        bool: ``__call__`` 返回 ``False``，让初始 tick 可继续从 stack 中处理。

    **该 filter 设计为配合** ``cerebro.replaydata`` **使用**。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='daily.csv')
    >>> data.addfilter(DaySplitter_Close, closevol=0.5)

    '''
    params = (
        ('closevol', 0.5),  # 保留给 close 的 volume 比例，范围 0 -> 1
    )

    # replaying = True

    def __init__(self, data):
        self.lastdt = None

    def __call__(self, data):
        # 复制新 bar，并从 stream 中移除
        datadt = data.datetime.date()  # 保留日期

        if self.lastdt == datadt:
            return False  # 跳过 filter 中再次出现的 bar

        self.lastdt = datadt  # 保留最近见到的 bar 引用

        # 复制当前 data，生成 ohlbar
        ohlbar = [data.lines[i][0] for i in range(data.size())]
        closebar = ohlbar[:]  # 为 close 生成副本

        # 用 o-h-l 平均值替换 close price
        ohlprice = ohlbar[data.Open] + ohlbar[data.High] + ohlbar[data.Low]
        ohlbar[data.Close] = ohlprice / 3.0

        vol = ohlbar[data.Volume]  # 调整 volume
        ohlbar[data.Volume] = vohl = int(vol * (1.0 - self.p.closevol))

        oi = ohlbar[data.OpenInterest]  # 调整 open interest
        ohlbar[data.OpenInterest] = 0

        # 调整时间
        dt = datetime.datetime.combine(datadt, data.p.sessionstart)
        ohlbar[data.DateTime] = data.date2num(dt)

        # 调整 closebar，生成单 tick -> close price
        closebar[data.Open] = cprice = closebar[data.Close]
        closebar[data.High] = cprice
        closebar[data.Low] = cprice
        closebar[data.Volume] = vol - vohl
        ohlbar[data.OpenInterest] = oi

        # 调整时间
        dt = datetime.datetime.combine(datadt, data.p.sessionend)
        closebar[data.DateTime] = data.date2num(dt)

        # 更新 stream
        data.backwards(force=True)  # 从 stream 移除已复制的 bar
        data._add2stack(ohlbar)  # 将 ohlbar 加入 stack
        # 将第 2 部分加入 stash，延后到下一轮处理
        data._add2stack(closebar, stash=True)

        return False  # 初始 tick 可继续从 stack 处理
