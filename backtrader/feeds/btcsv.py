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

from datetime import date, datetime, time

from .. import feed
from ..utils import date2num


class BacktraderCSVData(feed.CSVDataBase):
    '''解析 backtrader 自定义测试 CSV 格式的 data feed。

    Args:
        dataname: 要解析的文件名或 file-like 对象。

    Returns:
        bool: ``_loadline`` 成功解析一行时返回 ``True``。

    ---
    >>> data = BacktraderCSVData(dataname='2006-day-001.txt')
    '''

    def _loadline(self, linetokens):
        itoken = iter(linetokens)

        dttxt = next(itoken)  # 格式为 YYYY-MM-DD，跳过第 4 和第 7 个字符
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))

        if len(linetokens) == 8:
            tmtxt = next(itoken)  # 如果存在，格式为 HH:MM:SS，跳过第 3 和第 6 个字符
            tm = time(int(tmtxt[0:2]), int(tmtxt[3:5]), int(tmtxt[6:8]))
        else:
            tm = self.p.sessionend  # session 结束时间参数

        self.lines.datetime[0] = date2num(datetime.combine(dt, tm))
        self.lines.open[0] = float(next(itoken))
        self.lines.high[0] = float(next(itoken))
        self.lines.low[0] = float(next(itoken))
        self.lines.close[0] = float(next(itoken))
        self.lines.volume[0] = float(next(itoken))
        self.lines.openinterest[0] = float(next(itoken))

        return True


class BacktraderCSV(feed.CSVFeedBase):
    DataCls = BacktraderCSVData
