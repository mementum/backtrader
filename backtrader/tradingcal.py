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


from datetime import datetime, timedelta, time

from .metabase import MetaParams
from backtrader.utils.py3 import string_types, with_metaclass
from backtrader.utils import UTC

__all__ = ['TradingCalendarBase', 'TradingCalendar', 'PandasMarketCalendar']

# full time 转为 float 时有精度误差；如果 microseconds 使用 time.max 中定义的
# 999999，可能会滚到下一天。
_time_max = time(hour=23, minute=59, second=59, microsecond=999990)


MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
(ISONODAY, ISOMONDAY, ISOTUESDAY, ISOWEDNESDAY, ISOTHURSDAY, ISOFRIDAY,
 ISOSATURDAY, ISOSUNDAY) = range(8)

WEEKEND = [SATURDAY, SUNDAY]
ISOWEEKEND = [ISOSATURDAY, ISOSUNDAY]
ONEDAY = timedelta(days=1)


class TradingCalendarBase(with_metaclass(MetaParams, object)):
    '''trading calendar 的基类，用于定义交易日和 session 时间查询接口。'''

    def _nextday(self, day):
        '''返回 ``day`` 之后的下一个交易日及其 isocalendar 组件。

        Returns:
            tuple: ``(nextday, (year, week, weekday))``。
        '''
        raise NotImplementedError

    def schedule(self, day):
        '''返回给定交易日的开盘和收盘时间。

        Returns:
            tuple: ``(opening, closing)``，元素通常为 ``datetime.time`` 或
            ``datetime.datetime``。
        '''
        raise NotImplementedError

    def nextday(self, day):
        '''返回 ``day`` 之后的下一个交易日。'''
        return self._nextday(day)[0]  # 第 1 个返回元素是 next day

    def nextday_week(self, day):
        '''返回 ``day`` 之后下一个交易日所属的 ISO week number。'''
        self._nextday(day)[1][1]  # 第 2 个元素是 isocal / 0 - y, 1 - wk, 2 - day

    def last_weekday(self, day):
        '''如果给定 ``day`` 是本周最后一个交易日，则返回 ``True``。'''
        # next day 必须大于 day。如果 week 改变，即使周数变小（跨年），也足以说明换周
        return day.isocalendar()[1] != self._nextday(day)[1][1]

    def last_monthday(self, day):
        '''如果给定 ``day`` 是本月最后一个交易日，则返回 ``True``。'''
        # next day 必须大于 day。月份变化即表示换月
        return day.month != self._nextday(day)[0].month

    def last_yearday(self, day):
        '''如果给定 ``day`` 是本年最后一个交易日，则返回 ``True``。'''
        # next day 必须大于 day。年份变化即表示换年
        return day.year != self._nextday(day)[0].year


class TradingCalendar(TradingCalendarBase):
    '''简单 trading calendar 实现。

    Args:

      - ``open`` (default ``time.min``)

        常规 session start。

      - ``close`` (default ``time.max``)

        常规 session end。

      - ``holidays`` (default ``[]``)

        非交易日列表（``datetime.datetime`` 实例）。

      - ``earlydays`` (default ``[]``)

        提前收盘/特殊交易时间的日期列表。每个 tuple 形如
        ``(datetime.datetime, datetime.time, datetime.time)``。

      - ``offdays`` (default ``ISOWEEKEND``)

        市场不交易的 ISO weekday 列表（Monday: 1 -> Sunday: 7）。默认是周六和周日。

    Returns:
        TradingCalendar: 可按交易日查询 session 时间的 calendar。

    ---
    交互示例：
        >>> from datetime import datetime
        >>> cal = TradingCalendar()
        >>> cal.nextday(datetime(2024, 1, 5)).date()
        datetime.date(2024, 1, 8)

    '''
    params = (
        ('open', time.min),
        ('close', _time_max),
        ('holidays', []),  # 非交易日列表（date）
        ('earlydays', []),  # tuple 列表：(date, opentime, closetime)
        ('offdays', ISOWEEKEND),  # 非交易日列表（isoweekdays）
    )

    def __init__(self):
        self._earlydays = [x[0] for x in self.p.earlydays]  # 加速查找

    def _nextday(self, day):
        '''返回 ``day`` 之后的下一个交易日及其 isocalendar 组件。

        Returns:
            tuple: ``(nextday, (year, week, weekday))``。
        '''
        while True:
            day += ONEDAY
            isocal = day.isocalendar()
            if isocal[2] in self.p.offdays or day in self.p.holidays:
                continue

            return day, isocal

    def schedule(self, day, tz=None):
        '''返回给定交易日的开盘和收盘时间。

        调用该方法时，默认 ``day`` 是实际交易日。

        Returns:
            tuple: ``(opentime, closetime)``。
        '''
        while True:
            dt = day.date()
            try:
                i = self._earlydays.index(dt)
                o, c = self.p.earlydays[i][1:]
            except ValueError:  # 未找到
                o, c = self.p.open, self.p.close

            closing = datetime.combine(dt, c)
            if tz is not None:
                closing = tz.localize(closing).astimezone(UTC)
                closing = closing.replace(tzinfo=None)

            if day > closing:  # 当前时间超过 eos
                day += ONEDAY
                continue

            opening = datetime.combine(dt, o)
            if tz is not None:
                opening = tz.localize(opening).astimezone(UTC)
                opening = opening.replace(tzinfo=None)

            return opening, closing


class PandasMarketCalendar(TradingCalendarBase):
    '''``pandas_market_calendars`` 的 trading calendar wrapper。

    需要安装 ``pandas_market_calendars`` 包。

    Args:

      - ``calendar`` (default ``None``)

        ``calendar`` 参数接受：

        - string: 支持的 calendar 名称，例如 `NYSE`。wrapper 会尝试获取 calendar 实例。

        - calendar instance: 例如 ``get_calendar('NYSE')`` 返回的对象。

      - ``cachesize`` (default ``365``)

        为查询提前缓存的天数。

    参考：

      - https://github.com/rsheftel/pandas_market_calendars

      - http://pandas-market-calendars.readthedocs.io/

    '''
    params = (
        ('calendar', None),  # pandas_market_calendars 实例或交易所名称
        ('cachesize', 365),  # 提前缓存的天数
    )

    def __init__(self):
        self._calendar = self.p.calendar

        if isinstance(self._calendar, string_types):  # 使用传入的 market name
            import pandas_market_calendars as mcal
            self._calendar = mcal.get_calendar(self._calendar)

        import pandas as pd  # pandas_market_calendars 保证可用
        self.dcache = pd.DatetimeIndex([0.0])
        self.idcache = pd.DataFrame(index=pd.DatetimeIndex([0.0]))
        self.csize = timedelta(days=self.p.cachesize)

    def _nextday(self, day):
        '''返回 ``day`` 之后的下一个交易日及其 isocalendar 组件。

        Returns:
            tuple: ``(nextday, (year, week, weekday))``。
        '''
        day += ONEDAY
        while True:
            i = self.dcache.searchsorted(day)
            if i == len(self.dcache):
                # 保留 1 年 cache 以加速查找
                self.dcache = self._calendar.valid_days(day, day + self.csize)
                continue

            d = self.dcache[i].to_pydatetime()
            return d, d.isocalendar()

    def schedule(self, day, tz=None):
        '''返回给定交易日的开盘和收盘时间。

        调用该方法时，默认 ``day`` 是实际交易日。

        Returns:
            tuple: ``(opentime, closetime)``。
        '''
        while True:
            i = self.idcache.index.searchsorted(day.date())
            if i == len(self.idcache):
                # 保留 1 年 cache 以加速查找
                self.idcache = self._calendar.schedule(day, day + self.csize)
                continue

            st = (x.tz_localize(None) for x in self.idcache.iloc[i, 0:2])
            opening, closing = st  # 获取 utc naive times
            if day > closing:  # 传入时间已超过 sessionend
                day += ONEDAY  # 滚到下一天
                continue

            return opening.to_pydatetime(), closing.to_pydatetime()
