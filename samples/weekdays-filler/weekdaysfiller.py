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


class WeekDaysFiller(object):
    '''bar filler，用于为交易日补充缺失的工作日。'''
    # 日期比较的初始值
    ONEDAY = datetime.timedelta(days=1)
    lastdt = datetime.date.max - ONEDAY

    def __init__(self, data, fillclose=False):
        self.fillclose = fillclose
        self.voidbar = [float('Nan')] * data.size()  # init a void bar

    def __call__(self, data):
        '''为没有数据的工作日添加空 bar（NaN）或使用上一 close price 的 bar。

        Args:
          - ``data``: 要过滤/处理的数据源。

        Returns:
          bool: 始终返回 ``True``；bars 会被移除，即便随后重新放回 stack。
        '''
        dt = data.datetime.date()  # current date in int format
        lastdt = self.lastdt + self.ONEDAY  # move last seen data once forward

        while lastdt < dt:  # loop over gap bars
            if lastdt.isoweekday() < 6:  # Mon-Fri
                # 填充日期，并把新 bar 加入 stack
                if self.fillclose:
                    self.voidbar = [self.lastclose] * data.size()
                dtime = datetime.datetime.combine(lastdt, data.p.sessionend)
                self.voidbar[-1] = data.date2num(dtime)
                data._add2stack(self.voidbar[:])

            lastdt += self.ONEDAY  # move lastdt forward

        self.lastdt = dt  # keep a record of the last seen date

        self.lastclose = data.close[0]
        data._save2stack(erase=True)  # dt bar to the stack and out of stream
        return True  # bars are on the stack (new and original)
