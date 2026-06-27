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


class BarReplayer_Open(object):
    '''将一根 bar 拆成 open bar 和完整 OHLC bar 的 filter。

    拆分结果:

      - ``Open``: 使用原 bar 的 opening price 生成初始 price bar，四个 OHLC
        组件相等。该初始 bar 的 volume/openinterest 为 0。

      - ``OHLC``: 输出完整原始 bar，并保留原始 ``volume``/``openinterest``。

    该拆分可模拟 replay，而无需使用 *replay* filter。

    Args:
        无。

    Returns:
        bool: stream 长度未变化时返回 ``True``；输出 pending bar 时返回
        ``False``。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='daily.csv')
    >>> data.addfilter(BarReplayer_Open)
    '''
    def __init__(self, data):
        self.pendingbar = None
        data.resampling = 1
        data.replaying = True

    def __call__(self, data):
        ret = True

        # 复制新 bar，并从 stream 中移除
        newbar = [data.lines[i][0] for i in range(data.size())]
        data.backwards()  # 从 stream 中移除已复制的 bar

        openbar = newbar[:]  # 生成只有 open 的 bar
        o = newbar[data.Open]
        for field_idx in [data.High, data.Low, data.Close]:
            openbar[field_idx] = o

        # 将 open 阶段的 Volume/OpenInterest 置零
        openbar[data.Volume] = 0.0
        openbar[data.OpenInterest] = 0.0

        # 用 pending data 覆盖新的 data bar，起点除外
        if self.pendingbar is not None:
            data._updatebar(self.pendingbar)
            ret = False

        self.pendingbar = newbar  # 将 pending bar 更新为新 bar
        data._add2stack(openbar)  # 将 openbar 加入 stack 等待处理

        return ret  # stream 长度未变化

    def last(self, data):
        '''当 data 不再产生 bar 时调用。

        该方法可以被多次调用，可用于输出额外 bar。

        Args:
            data: 要处理的 data source。

        Returns:
            bool: 输出 pending bar 时返回 ``True``；没有可输出内容时返回
            ``False``。
        '''
        if self.pendingbar is not None:
            data.backwards()  # 移除已交付的 open bar
            data._add2stack(self.pendingbar)  # 加入剩余 bar
            self.pendingbar = None  # 无需进一步动作
            return True  # 已交付内容

        return False  # 此处没有交付内容


# Alias
DayStepsFilter = BarReplayer_Open
