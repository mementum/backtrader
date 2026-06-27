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

from .. import feed
from .. import TimeFrame
from ..utils import date2num


class VChartCSVData(feed.CSVDataBase):
    '''
    解析 `VisualChart <http://www.visualchart.com>`_ 导出的 CSV 文件。

    Args:
        dataname: 要解析的文件名，或已经打开的类文件对象。

    Returns:
        VChartCSVData: 可加入 Cerebro 的 VisualChart CSV 数据源实例。

    ---
    交互界面使用示范:

    >>> data = VChartCSVData(dataname='visualchart.csv')
    >>> data.p.dataname
    'visualchart.csv'
    '''

    vctframes = dict(
        I=TimeFrame.Minutes,
        D=TimeFrame.Days,
        W=TimeFrame.Weeks,
        M=TimeFrame.Months)

    def _loadline(self, linetokens):
        itokens = iter(linetokens)

        ticker = next(itokens)  # 跳过 ticker 名称
        if not self._name:
            self._name = ticker

        # 日线/日内数据标记
        timeframe = next(itokens)

        self._timeframe = self.vctframes[timeframe]

        dttxt = next(itokens)
        y, m, d = int(dttxt[0:4]), int(dttxt[4:6]), int(dttxt[6:8])

        tmtxt = next(itokens)
        if timeframe == 'I':
            # 日内数据使用文件提供的时间
            hh, mmss = divmod(int(tmtxt), 10000)
            mm, ss = divmod(mmss, 100)
        else:
            # 日线及以上周期放到 sessionend 指定的收盘时间
            hh = self.p.sessionend.hour
            mm = self.p.sessionend.minute
            ss = self.p.sessionend.second

        dtnum = date2num(datetime.datetime(y, m, d, hh, mm, ss))

        self.lines.datetime[0] = dtnum
        self.lines.open[0] = float(next(itokens))
        self.lines.high[0] = float(next(itokens))
        self.lines.low[0] = float(next(itokens))
        self.lines.close[0] = float(next(itokens))
        self.lines.volume[0] = float(next(itokens))
        self.lines.openinterest[0] = float(next(itokens))

        return True


class VChartCSV(feed.CSVFeedBase):
    DataCls = VChartCSVData
