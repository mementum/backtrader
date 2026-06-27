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

import datetime as _datetime
from datetime import datetime
import inspect

from .utils.py3 import range, with_metaclass
from .lineseries import LineSeries
from .utils import AutoOrderedDict, OrderedDict, date2num


class TimeFrame(object):
    '''timeframe 枚举容器，用于统一表示 data 的时间粒度。'''

    (Ticks, MicroSeconds, Seconds, Minutes,
     Days, Weeks, Months, Years, NoTimeFrame) = range(1, 10)

    Names = ['', 'Ticks', 'MicroSeconds', 'Seconds', 'Minutes',
             'Days', 'Weeks', 'Months', 'Years', 'NoTimeFrame']

    names = Names  # support old naming convention

    @classmethod
    def getname(cls, tframe, compression=None):
        '''返回 timeframe 名称，并在 compression 为 1 时使用单数形式。'''
        tname = cls.Names[tframe]
        if compression > 1 or tname == cls.Names[-1]:
            return tname  # 复数或 'NoTimeFrame' 直接返回原条目

        # compression 为 1 时返回单数形式
        return cls.Names[tframe][:-1]

    @classmethod
    def TFrame(cls, name):
        return getattr(cls, name)

    @classmethod
    def TName(cls, tframe):
        return cls.Names[tframe]


class DataSeries(LineSeries):
    '''data series 的基类，用于提供 OHLCV line、timeframe 和 writer 输出信息。'''

    plotinfo = dict(plot=True, plotind=True, plotylimited=True)

    _name = ''
    _compression = 1
    _timeframe = TimeFrame.Days

    Close, Low, High, Open, Volume, OpenInterest, DateTime = range(7)

    LineOrder = [DateTime, Open, High, Low, Close, Volume, OpenInterest]

    def getwriterheaders(self):
        headers = [self._name, 'len']

        for lo in self.LineOrder:
            headers.append(self._getlinealias(lo))

        morelines = self.getlinealiases()[len(self.LineOrder):]
        headers.extend(morelines)

        return headers

    def getwritervalues(self):
        l = len(self)
        values = [self._name, l]

        if l:
            values.append(self.datetime.datetime(0))
            for line in self.LineOrder[1:]:
                values.append(self.lines[line][0])
            for i in range(len(self.LineOrder), self.lines.size()):
                values.append(self.lines[i][0])
        else:
            values.extend([''] * self.lines.size())  # 尚无 values

        return values

    def getwriterinfo(self):
        # 返回包含 data 描述信息的 dictionary
        info = OrderedDict()
        info['Name'] = self._name
        info['Timeframe'] = TimeFrame.TName(self._timeframe)
        info['Compression'] = self._compression

        return info


class OHLC(DataSeries):
    '''OHLCV data series 的基类，用于定义标准价格与成交量 line。'''

    lines = ('close', 'low', 'high', 'open', 'volume', 'openinterest',)


class OHLCDateTime(OHLC):
    '''带 datetime line 的 OHLC data series 基类。'''

    lines = (('datetime'),)


class SimpleFilterWrapper(object):
    '''filter wrapper，用于把通过 ``.addfilter`` 添加的 filter 转成 processor。

    filter 是 callable，约定如下：

      - 接收 ``data`` 作为参数
      - 当前 bar 未触发 filter 时返回 ``False``
      - 当前 bar 必须被过滤时返回 ``True``

    wrapper 会读取返回值，并在需要时执行 bar removal。

    Args:
        data: 绑定的 data feed。
        ffilter: filter callable 或 filter class。
        *args: 传给 filter 的位置参数。
        **kwargs: 传给 filter 的关键字参数。

    Returns:
        SimpleFilterWrapper: 可被 data feed 调用的 filter wrapper。

    ---
    交互示例：
        >>> class Data:
        ...     def __init__(self):
        ...         self.backwards_called = False
        ...     def backwards(self):
        ...         self.backwards_called = True
        >>> data = Data()
        >>> wrapper = SimpleFilterWrapper(data, lambda data: True)
        >>> wrapper(data)
        True
        >>> data.backwards_called
        True
    '''
    def __init__(self, data, ffilter, *args, **kwargs):
        if inspect.isclass(ffilter):
            ffilter = ffilter(data, *args, **kwargs)
            args = []
            kwargs = {}

        self.ffilter = ffilter
        self.args = args
        self.kwargs = kwargs

    def __call__(self, data):
        if self.ffilter(data, *self.args, **self.kwargs):
            data.backwards()
            return True

        return False


class _Bar(AutoOrderedDict):
    '''DataBase 标准 line 值的占位容器。

    该类保存 ``OHLCDateTime`` 标准 line 的当前 bar 值，并继承 ``AutoOrderedDict``，
    以便按 iterable 返回 values，同时支持按属性访问 key。

    定义顺序很重要，必须与 ``DataBase`` 中继承自 ``OHLCDateTime`` 的 line 定义一致。

    ---
    交互示例：
        >>> bar = _Bar()
        >>> bar.isopen()
        False
        >>> bar.volume
        0.0
    '''
    replaying = False

    # 如果不减 1，转换回 time 会失败。
    # 额外再减 1，用于支持可能把 time 向前移动的 timezone。
    MAXDATE = date2num(_datetime.datetime.max) - 2

    def __init__(self, maxdate=False):
        super(_Bar, self).__init__()
        self.bstart(maxdate=maxdate)

    def bstart(self, maxdate=False):
        '''将 bar 初始化为默认的未更新值。'''
        # 顺序很重要：由 DataSeries/OHLC/OHLCDateTime 定义
        self.close = float('NaN')
        self.low = float('inf')
        self.high = float('-inf')
        self.open = float('NaN')
        self.volume = 0.0
        self.openinterest = 0.0
        self.datetime = self.MAXDATE if maxdate else None

    def isopen(self):
        '''返回 bar 是否已经被更新。

        该方法利用 NaN 不等于自身的事实；``open`` 初始化为 NaN。
        '''
        o = self.open
        return o == o  # NaN 时为 False，其它情况为 True

    def bupdate(self, data, reopen=False):
        '''使用 data 中的值更新当前 bar。

        Args:
            data: 提供 OHLCV 当前值的 data feed。
            reopen: 是否先重新初始化 bar。

        Returns:
            bool: 如果这是该 bar 的首次更新（刚打开）则返回 ``True``，否则返回 ``False``。
        '''
        if reopen:
            self.bstart()

        self.datetime = data.datetime[0]

        self.high = max(self.high, data.high[0])
        self.low = min(self.low, data.low[0])
        self.close = data.close[0]

        self.volume += data.volume[0]
        self.openinterest = data.openinterest[0]

        o = self.open
        if reopen or not o == o:
            self.open = data.open[0]
            return True  # 刚打开 bar

        return False
