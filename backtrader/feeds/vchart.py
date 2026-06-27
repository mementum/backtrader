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
import struct
import os.path

from .. import feed
from .. import TimeFrame
from ..utils import date2num


class VChartData(feed.DataBase):
    '''
    支持 `Visual Chart <www.visualchart.com>`_ 的本地二进制文件，包括日线和日内
    数据格式。

    Args:
        dataname: 文件路径，或已经打开的类文件对象。传入类文件对象时，使用
            ``timeframe`` 参数判断实际 timeframe；传入路径时，优先根据扩展名
            判断，``.fd`` 表示日线，``.min`` 表示日内数据。

    Returns:
        VChartData: 可加入 Cerebro 的 Visual Chart 数据源实例。

    ---
    交互界面使用示范:

    >>> data = VChartData(dataname='010015ES.fd')
    >>> data.p.dataname
    '010015ES.fd'
    '''

    def start(self):
        super(VChartData, self).start()

        # 先记录扩展名，后面根据 dataname 和 timeframe 决定是否补全
        self.ext = ''

        if not hasattr(self.p.dataname, 'read'):
            # 没有 read 方法时按字符串路径处理

            if self.p.dataname.endswith('.fd'):
                self.p.timeframe = TimeFrame.Days
            elif self.p.dataname.endswith('.min'):
                self.p.timeframe = TimeFrame.Minutes
            else:
                # 没有 fd/min 扩展名时，根据 timeframe 自动补扩展名
                if self.p.timeframe == TimeFrame.Days:
                    self.ext = '.fd'
                else:
                    self.ext = '.min'

        if self.p.timeframe >= TimeFrame.Days:
            self.barsize = 28
            self.dtsize = 1
            self.barfmt = 'IffffII'
        else:
            self.dtsize = 2
            self.barsize = 32
            self.barfmt = 'IIffffII'

        self.f = None
        if hasattr(self.p.dataname, 'read'):
            # 已经传入打开的文件对象，例如来自 GUI 的文件选择器
            self.f = self.p.dataname
        else:
            dataname = self.p.dataname + self.ext
            # 打不开文件时让异常向上传递，调用方能看到真实原因
            self.f = open(dataname, 'rb')

    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None

    def _load(self):
        if self.f is None:
            return False

        # 读取失败时让异常向上传递，调用方能看到真实原因
        bardata = self.f.read(self.barsize)
        if not bardata:
            return False

        bdata = struct.unpack(self.barfmt, bardata)

        # 年份按“每年 500 天”的编码方式存储
        y, md = divmod(bdata[0], 500)
        # 月份按“每月 32 天”的编码方式存储
        m, d = divmod(md, 32)
        dt = datetime.datetime(y, m, d)

        if self.dtsize > 1:  # 分钟 bar
            # 日内时间以秒数存储
            hhmm, ss = divmod(bdata[1], 60)
            hh, mm = divmod(hhmm, 60)
            dt = dt.replace(hour=hh, minute=mm, second=ss)

        self.lines.datetime[0] = date2num(dt)

        o, h, l, c, v, oi = bdata[self.dtsize:]
        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        self.lines.openinterest[0] = oi

        return True


class VChartFeed(feed.FeedBase):
    DataCls = VChartData

    params = (('basepath', ''),) + DataCls.params._gettuple()

    def _getdata(self, dataname, **kwargs):
        maincode = dataname[0:2]
        subcode = dataname[2:6]

        datapath = os.path.join(self.p.basepath,
                                'RealServer', 'Data',
                                maincode, subcode,  # 01 00XX
                                dataname)

        newkwargs = self.p._getkwargs()
        newkwargs.update(kwargs)
        kwargs['dataname'] = datapath
        return self.DataCls(**kwargs)
