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
import math
import time as _time

from .py3 import string_types


ZERO = datetime.timedelta(0)

STDOFFSET = datetime.timedelta(seconds=-_time.timezone)
if _time.daylight:
    DSTOFFSET = datetime.timedelta(seconds=-_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

# 避免 rounding error 把日期推到下一天
TIME_MAX = datetime.time(23, 59, 59, 999990)

# 避免 rounding error 把日期推到下一天
TIME_MIN = datetime.time.min


def tzparse(tz):
    '''解析 timezone 参数。

    Args:
        tz: ``None``、timezone 对象或 timezone 名称。

    Returns:
        timezone: 可用的 timezone/localizer 对象，或原值的 localizer 包装。
    '''
    # 如果用户未提供对象，但可通过 contract details 找到 timezone，
    # 则尝试从 pytz 获取；pytz 可能可用也可能不可用。
    tzstr = isinstance(tz, string_types)
    if tz is None or not tzstr:
        return Localizer(tz)

    try:
        import pytz  # 保持 import 非常局部
    except ImportError:
        return Localizer(tz)    # 无法进一步处理

    tzs = tz
    if tzs == 'CST':  # 常见别名
        tzs = 'CST6CDT'

    try:
        tz = pytz.timezone(tzs)
    except pytz.UnknownTimeZoneError:
        return Localizer(tz)    # 无法进一步处理

    return tz


def Localizer(tz):
    '''确保 timezone 对象拥有 ``localize`` 方法。'''
    import types

    def localize(self, dt):
        return dt.replace(tzinfo=self)

    if tz is not None and not hasattr(tz, 'localize'):
        # 用 bound method patch tz 实例
        tz.localize = types.MethodType(localize, tz)

    return tz


# UTC 类，与 Python Docs 中的实现一致
class _UTC(datetime.tzinfo):
    """UTC timezone 实现。"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

    def localize(self, dt):
        return dt.replace(tzinfo=self)


class _LocalTimezone(datetime.tzinfo):
    '''本地 timezone 实现，用于根据系统 DST 规则计算 offset。'''

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        try:
            stamp = _time.mktime(tt)
        except (ValueError, OverflowError):
            return False  # 距离未来太远，不相关

        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0

    def localize(self, dt):
        return dt.replace(tzinfo=self)


UTC = _UTC()
TZLocal = _LocalTimezone()


HOURS_PER_DAY = 24.0
MINUTES_PER_HOUR = 60.0
SECONDS_PER_MINUTE = 60.0
MUSECONDS_PER_SECOND = 1e6
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY
SECONDS_PER_DAY = SECONDS_PER_MINUTE * MINUTES_PER_DAY
MUSECONDS_PER_DAY = MUSECONDS_PER_SECOND * SECONDS_PER_DAY


def num2date(x, tz=None, naive=True):
    # 与 matplotlib 类似，但 tz 为 None 时返回 naive datetime object。
    """将 float 日期数转换为 ``datetime``。

    ``x`` 是从 ``0001-01-01 00:00:00 UTC`` 加一天后开始计算的天数；
    小数部分表示 hours、minutes、seconds。这里额外加一天是历史遗留行为。
    该函数假设使用 Gregorian calendar。

    Args:
        x: float 日期数。
        tz: 可选 timezone。
        naive: 指定 tz 时是否移除返回值上的 ``tzinfo``。

    Returns:
        datetime.datetime: 转换后的 datetime。

    ---
    交互示例：
        >>> num2date(date2num(datetime.datetime(2024, 1, 2, 3, 4, 5)))
        datetime.datetime(2024, 1, 2, 3, 4, 5)
    """

    ix = int(x)
    dt = datetime.datetime.fromordinal(ix)
    remainder = float(x) - ix
    hour, remainder = divmod(HOURS_PER_DAY * remainder, 1)
    minute, remainder = divmod(MINUTES_PER_HOUR * remainder, 1)
    second, remainder = divmod(SECONDS_PER_MINUTE * remainder, 1)
    microsecond = int(MUSECONDS_PER_SECOND * remainder)
    if microsecond < 10:
        microsecond = 0  # compensate for rounding errors

    if True and tz is not None:
        dt = datetime.datetime(
            dt.year, dt.month, dt.day, int(hour), int(minute), int(second),
            microsecond, tzinfo=UTC)
        dt = dt.astimezone(tz)
        if naive:
            dt = dt.replace(tzinfo=None)
    else:
        # 未传入 tz 时返回不带 timezone 的 dt
        dt = datetime.datetime(
            dt.year, dt.month, dt.day, int(hour), int(minute), int(second),
            microsecond)

    if microsecond > 999990:  # compensate for rounding errors
        dt += datetime.timedelta(microseconds=1e6 - microsecond)

    return dt


def num2dt(num, tz=None, naive=True):
    '''将 numeric 日期转换为 ``datetime.date``。'''
    return num2date(num, tz=tz, naive=naive).date()


def num2time(num, tz=None, naive=True):
    '''将 numeric 日期转换为 ``datetime.time``。'''
    return num2date(num, tz=tz, naive=naive).time()


def date2num(dt, tz=None):
    """将 ``datetime`` 转换为 Gregorian UTC float days。

    会保留 hours、minutes、seconds 和 microseconds。

    Args:
        dt: ``datetime.datetime`` 或 ``datetime.date``。
        tz: 可选 timezone；传入时先 localize。

    Returns:
        float: 转换后的日期数。

    ---
    交互示例：
        >>> date2num(datetime.datetime(2024, 1, 1))
        738886.0
    """
    if tz is not None:
        dt = tz.localize(dt)

    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        delta = dt.tzinfo.utcoffset(dt)
        if delta is not None:
            dt -= delta

    base = float(dt.toordinal())
    if hasattr(dt, 'hour'):
        # base += (dt.hour / HOURS_PER_DAY +
        #          dt.minute / MINUTES_PER_DAY +
        #          dt.second / SECONDS_PER_DAY +
        #          dt.microsecond / MUSECONDS_PER_DAY
        #         )
        base = math.fsum(
            (base, dt.hour / HOURS_PER_DAY, dt.minute / MINUTES_PER_DAY,
             dt.second / SECONDS_PER_DAY, dt.microsecond / MUSECONDS_PER_DAY))

    return base


def time2num(tm):
    """将 time 或 datetime 的日内部分转换为 numeric fraction。

    Args:
        tm: ``datetime.datetime`` 或 ``datetime.time``。

    Returns:
        float: 日内时间对应的一天内比例。

    ---
    交互示例：
        >>> time2num(datetime.time(12, 0))
        0.5
    """
    num = (tm.hour / HOURS_PER_DAY +
           tm.minute / MINUTES_PER_DAY +
           tm.second / SECONDS_PER_DAY +
           tm.microsecond / MUSECONDS_PER_DAY)

    return num
