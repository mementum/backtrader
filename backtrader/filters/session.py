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

from datetime import datetime, timedelta

from backtrader import TimeFrame
from backtrader.utils.py3 import with_metaclass
from .. import metabase


class SessionFiller(with_metaclass(metabase.MetaParams, object)):
    '''在声明的 session start/end 时间内为 data source 补 bar 的 Bar Filler。

    补出的 bar 会使用 data source 声明的 ``timeframe`` 和 ``compression``
    来计算缺失时间点。

    Args:
        fill_price: 缺失 bar 使用的价格，默认 ``None``。如果为 ``None``，
            使用上一根 bar 的 close。也可以传入 ``float('NaN')``，让该 bar
            占用时间但不在图上显示出有效价格。
        fill_vol: 缺失 bar 使用的 volume，默认 ``NaN``。
        fill_oi: 缺失 bar 使用的 open interest，默认 ``NaN``。
        skip_first_fill (bool): 看到第 1 根有效 bar 时，是否跳过从
            sessionstart 到该 bar 的填补，默认 ``True``。

    Returns:
        None: filter 会把补出的 bar 加入 data stack。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='intraday.csv',
    ...                                timeframe=bt.TimeFrame.Minutes)
    >>> data.addfilter(SessionFiller, fill_vol=0.0)
    '''
    params = (('fill_price', None),
              ('fill_vol', float('NaN')),
              ('fill_oi', float('NaN')),
              ('skip_first_fill', True))

    MAXDATE = datetime.max

    # bar 之间的最小 delta 单位
    _tdeltas = {
        TimeFrame.Minutes: timedelta(seconds=60),
        TimeFrame.Seconds: timedelta(seconds=1),
        TimeFrame.MicroSeconds: timedelta(microseconds=1),
    }

    def __init__(self, data):
        # 计算并保存 timeframe 对应的 timedelta
        self._tdframe = self._tdeltas[data._timeframe]
        self._tdunit = self._tdeltas[data._timeframe] * data._compression

        self.seenbar = False  # 控制是否至少见过一根 bar
        self.sessend = self.MAXDATE  # maxdate 是 session bar 的控制标记

    def __call__(self, data):
        '''处理一根 data bar，并按 session 边界补出缺失 bar。

        Args:
            data: 要过滤/处理的 data source。

        Returns:
            bool: 添加了补 bar 或需要重新处理 stream 时返回 ``True``；否则返回
            ``False``。

        逻辑从 ``MAXDATE`` 作为 session end 控制标记开始:

          - 如果新 bar 超过 session end（第 1 根 bar 不会出现这种情况），
            补到 session end，并将 session end 重置为 ``MAXDATE`` 后继续。

          - 如果 session end 标记为 ``MAXDATE``，重新计算 session 边界，
            检查 bar 是否在边界内；如果在，补齐并记录最后看到的时间。

          - 否则 incoming bar 位于 session 内，补到该 bar 为止。
        '''
        # 获取当前底层 data source bar 的时间
        ret = False

        dtime_cur = data.datetime.datetime()

        if dtime_cur > self.sessend:
            # bar 超过 session end，补齐并使控制标记失效
            # 不把当前 bar 放入 stack，让它在下方继续被评估
            # 补到 session end + timeframe 最小单位
            ret = self._fillbars(data, self.dtime_prev,
                                 self.sessend + self._tdframe,
                                 tostack=False)
            self.sessend = self.MAXDATE

        # 从前一检查继续：超过旧 session 的 bar 可能已经处于新 session 内
        if self.sessend == self.MAXDATE:
            # 尚未见过 bar，或某根 bar 超过了上一 session 边界
            ddate = dtime_cur.date()
            sessstart = datetime.combine(ddate, data.p.sessionstart)
            self.sessend = sessend = datetime.combine(ddate, data.p.sessionend)

            if sessstart <= dtime_cur <= sessend:
                # session 内的第 1 根 bar：从 session start 开始填补
                if self.seenbar or not self.p.skip_first_fill:
                    ret = self._fillbars(data,
                                         sessstart - self._tdunit, dtime_cur)

            self.seenbar = True
            self.dtime_prev = dtime_cur

        else:
            # 已见过前一根 bar，且当前 bar 在 session 内：补到当前 bar
            ret = self._fillbars(data, self.dtime_prev, dtime_cur)
            self.dtime_prev = dtime_cur

        return ret

    def _fillbars(self, data, time_start, time_end, tostack=True):
        '''按需逐根填补从 ``time_start`` 到 ``time_end`` 之间的 bar。

        Args:
            data: 要补 bar 的 data source。
            time_start: 填补起始时间。
            time_end: 填补结束时间。
            tostack (bool): 是否把触发填补的 bar 保存回 stack。

        Returns:
            bool: 有补 bar 或 ``tostack`` 为 ``False`` 时返回 ``True``。
        '''
        # 控制标记：是否有 bar 加入 stack
        dirty = 0

        time_start += self._tdunit
        while time_start < time_end:
            dirty += self._fillbar(data, time_start)
            time_start += self._tdunit

        if dirty and tostack:
            data._save2stack(erase=True)

        return bool(dirty) or not tostack

    def _fillbar(self, data, dtime):
        # 准备所需大小的数组
        bar = [float('Nan')] * data.size()

        # 填充 datetime
        bar[data.DateTime] = data.date2num(dtime)

        # 填充 price
        price = self.p.fill_price or data.close[-1]
        for pricetype in [data.Open, data.High, data.Low, data.Close]:
            bar[pricetype] = price

        # 填充 volume 和 open interest
        bar[data.Volume] = self.p.fill_vol
        bar[data.OpenInterest] = self.p.fill_oi

        # 填充 data feed 可能在 DateTime 之后定义的额外 lines
        for i in range(data.DateTime + 1, data.size()):
            bar[i] = data.lines[i][0]

        # 加入待保存 bar stack
        data._add2stack(bar)

        return True


class SessionFilterSimple(with_metaclass(metabase.MetaParams, object)):
    '''过滤常规 session 时间之外日内 bar 的 simple filter。

    该 filter 可应用到 data source，用于过滤 pre/post market data 等常规
    session 之外的日内 bar。

    这是 "simple" filter，不管理传入 ``__init__`` 和 ``__call__`` 的 data
    stack。它没有需要额外交付的数据，因此不需要 ``last`` 方法。Bar
    management 会由 ``DataBase.addfilter_simple`` 添加的
    ``SimpleFilterWrapper`` 完成。

    Args:
        无。

    Returns:
        bool: 当前 bar 在 session 内返回 ``False``；在 session 外返回
        ``True``，表示过滤当前 bar。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='intraday.csv')
    >>> data.addfilter_simple(SessionFilterSimple)
    '''
    def __init__(self, data):
        pass

    def __call__(self, data):
        '''判断当前 bar 是否应被过滤。

        Args:
            data: 要过滤/处理的 data source。

        Returns:
            bool: ``False`` 表示无需过滤；``True`` 表示当前 bar 不在 session
            时间内，应被过滤。
        '''
        # 比较的两端都位于 session 中
        return not (
            data.p.sessionstart <= data.datetime.time(0) <= data.p.sessionend)


class SessionFilter(with_metaclass(metabase.MetaParams, object)):
    '''过滤常规 session 时间之外日内 bar 的非 simple filter。

    该 filter 可应用到 data source，用于过滤 pre/post market data 等常规
    session 之外的日内 bar。

    这是 "non-simple" filter，必须管理传入 ``__init__`` 和 ``__call__`` 的
    data stack。它没有需要额外交付的数据，因此不需要 ``last`` 方法。

    Args:
        无。

    Returns:
        bool: 当前 bar 在 session 内返回 ``False``；在 session 外移除 bar 并
        返回 ``True``。

    ---
    >>> import backtrader as bt
    >>> data = bt.feeds.GenericCSVData(dataname='intraday.csv')
    >>> data.addfilter(SessionFilter)
    '''
    def __init__(self, data):
        pass

    def __call__(self, data):
        '''判断并处理当前 bar 是否应被过滤。

        Args:
            data: 要过滤/处理的 data source。

        Returns:
            bool: ``False`` 表示 data stream 未改动；``True`` 表示 data stream
            已被改动，即 session 时间外的 bar 已被移除。
        '''
        if data.p.sessionstart <= data.datetime.time(0) <= data.p.sessionend:
            # 比较的两端都位于 session 中
            return False  # 表示 stream 未改动

        # bar 位于常规 session 时间之外
        data.backwards()  # 从 data stack 移除 bar
        return True  # 表示 data 已被改动
