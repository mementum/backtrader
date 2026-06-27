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
import datetime
import math


import backtrader as bt


class RelativeVolumeByBar(bt.Indicator):
    alias = ('RVBB',)
    lines = ('rvbb',)

    params = (
        ('prestart', datetime.time(8, 00)),
        ('start', datetime.time(9, 10)),
        ('end', datetime.time(17, 15)),
    )

    def _plotlabel(self):
        plabels = []
        for name, value in self.params._getitems():
            plabels.append('%s: %s' % (name, value.strftime('%H:%M')))

        return plabels

    def __init__(self):
        # 通知平台所需的 minimum period
        minbuffer = self._calcbuffer()
        self.addminperiod(minbuffer)

        # 用于保持同步的结构/变量
        self.pvol = dict()
        self.vcount = collections.defaultdict(int)

        self.days = 0
        self.dtlast = datetime.date.min

        # 在计算后完成，以确保协作继承和组合正常工作
        super(RelativeVolumeByBar, self).__init__()

    def _barisvalid(self, tm):
        return self.p.start <= tm <= self.p.end

    def _daycount(self):
        dt = self.data.datetime.date()
        if dt > self.dtlast:
            self.days += 1
            self.dtlast = dt

    def prenext(self):
        self._daycount()

        tm = self.data.datetime.time()
        if self._barisvalid(tm):
            self.pvol[tm] = self.data.volume[0]
            self.vcount[tm] += 1

    def next(self):
        self._daycount()

        tm = self.data.datetime.time()
        if not self._barisvalid(tm):
            return

        # 记录当天已出现的 "minute/second"
        self.vcount[tm] += 1

        # 获取 bar 的 volume
        vol = self.data.volume[0]

        # 如果天数正确，说明上一天见过相同 "minute/second"
        if self.vcount[tm] == self.days:
            self.lines.rvbb[0] = vol / self.pvol[tm]

        # 同步 days 和 volume count，供下一轮使用
        self.vcount[tm] = self.days

        # 记录当前 bar 的 volume，供下一轮使用
        self.pvol[tm] = vol

    def _calcbuffer(self):
        # period 计算
        minend = self.p.end.hour * 60 + self.p.end.minute
        # minstart = session_start.hour * 60 + session_start.minute
        # 使用 prestart 以考虑 market_data
        minstart = self.p.prestart.hour * 60 + self.p.prestart.minute

        minbuffer = minend - minstart

        tframe = self.data._timeframe
        tcomp = self.data._compression

        if tframe == bt.TimeFrame.Seconds:
            minbuffer = (minperiod * 60)

        minbuffer = (minbuffer // tcomp) + tcomp

        return minbuffer
