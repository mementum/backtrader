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

from datetime import datetime
from struct import unpack
import os.path

import backtrader as bt
from backtrader import date2num  # 避免字典查找


class MetaVChartFile(bt.DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，随后把它注册到对应 store。'''
        # 初始化类对象
        super(MetaVChartFile, cls).__init__(name, bases, dct)

        # 注册到 store，供 VChartFile store 找到实际 DataCls
        bt.stores.VChartFile.DataCls = cls


class VChartFile(bt.with_metaclass(MetaVChartFile, bt.DataBase)):
    '''
    支持 `Visual Chart <www.visualchart.com>`_ 的本地二进制文件，包括日线和日内
    数据格式。

    Args:
        dataname: Visual Chart 显示的市场代码。例如 ``015ES`` 表示 EuroStoxx
            50 连续期货。

    Returns:
        VChartFile: 可加入 Cerebro 的 Visual Chart 文件数据源实例。

    ---
    交互界面使用示范:

    >>> data = VChartFile(dataname='015ES')
    >>> data.p.dataname
    '015ES'
    '''

    def start(self):
        super(VChartFile, self).start()
        if self._store is None:
            self._store = bt.stores.VChartFile()
            self._store.start()

        self._store.start(data=self)

        # 根据 timeframe 选择扩展名和解析参数
        if self.p.timeframe < bt.TimeFrame.Minutes:
            ext = '.tck'  # 秒级数据仍需要 resampling
            # FIXME: 找到 tick 计数器格式的参考资料
        elif self.p.timeframe < bt.TimeFrame.Days:
            ext = '.min'
            self._dtsize = 2
            self._barsize = 32
            self._barfmt = 'IIffffII'
        else:
            ext = '.fd'
            self._barsize = 28
            self._dtsize = 1
            self._barfmt = 'IffffII'

        # 拼出完整文件路径
        basepath = self._store.get_datapath()

        # 例如：01 + 0 + 015ES + .fd -> 010015ES.fd
        dataname = '01' + '0' + self.p.dataname + ext
        # 015ES -> 0 + 015 -> 0015
        mktcode = '0' + self.p.dataname[0:3]

        # basepath/0015/010015ES.fd
        path = os.path.join(basepath, mktcode, dataname)
        try:
            self.f = open(path, 'rb')
        except IOError:
            self.f = None

    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None

    def _load(self):
        if self.f is None:
            return False  # 没有更多数据可加载

        try:
            bardata = self.f.read(self._barsize)
        except IOError:
            self.f = None  # 无法继续读取，清空文件对象
            return False  # 没有更多数据可加载

        if not bardata or len(bardata) < self._barsize:
            self.f = None  # 无法继续读取，清空文件对象
            return False  # 没有更多数据可加载

        try:
            bdata = unpack(self._barfmt, bardata)
        except:
            self.f = None
            return False

        # 先解析日期
        y, md = divmod(bdata[0], 500)  # 年份按“每年 500 天”的编码方式存储
        m, d = divmod(md, 32)  # 月份按“每月 32 天”的编码方式存储
        dt = datetime(y, m, d)

        # 再解析时间
        if self._dtsize > 1:  # 分钟 bar
            # 日内时间以秒数存储
            hhmm, ss = divmod(bdata[1], 60)
            hh, mm = divmod(hhmm, 60)
            dt = dt.replace(hour=hh, minute=mm, second=ss)
        else:  # 日线 bar
            dt = datetime.combine(dt, self.p.sessionend)

        self.lines.datetime[0] = date2num(dt)  # 存储时间

        # 读取剩余字段
        o, h, l, c, v, oi = bdata[self._dtsize:]
        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        self.lines.openinterest[0] = oi

        return True  # 成功加载了一个 bar
