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

'''
Redefine/Override matplotlib locators to make them work with index base x axis
which can be converted from/to dates
'''

import datetime
import warnings

from matplotlib.dates import AutoDateLocator as ADLocator
from matplotlib.dates import RRuleLocator as RRLocator
from matplotlib.dates import AutoDateFormatter as ADFormatter

from matplotlib.dates import (HOURS_PER_DAY, MIN_PER_HOUR, SEC_PER_MIN,
                              MONTHS_PER_YEAR, DAYS_PER_WEEK,
                              SEC_PER_HOUR, SEC_PER_DAY,
                              num2date, rrulewrapper, YearLocator,
                              MicrosecondLocator)

from dateutil.relativedelta import relativedelta
import numpy as np


def _idx2dt(idx, dates, tz):
    if isinstance(idx, datetime.date):
        return idx

    ldates = len(dates)

    idx = int(round(idx))
    if idx >= ldates:
        idx = ldates - 1
    if idx < 0:
        idx = 0

    return num2date(dates[idx], tz)


class RRuleLocator(RRLocator):

    def __init__(self, dates, o, tz=None):
        self._dates = dates
        super(RRuleLocator, self).__init__(o, tz)

    def datalim_to_dt(self):
        """
        Convert axis data interval to datetime objects.
        """
        dmin, dmax = self.axis.get_data_interval()
        if dmin > dmax:
            dmin, dmax = dmax, dmin

        return (_idx2dt(dmin, self._dates, self.tz),
                _idx2dt(dmax, self._dates, self.tz))

    def viewlim_to_dt(self):
        """
        Converts the view interval to datetime objects.
        """
        vmin, vmax = self.axis.get_view_interval()
        if vmin > vmax:
            vmin, vmax = vmax, vmin

        return (_idx2dt(vmin, self._dates, self.tz),
                _idx2dt(vmax, self._dates, self.tz))

    def tick_values(self, vmin, vmax):
        import bisect
        dtnums = super(RRuleLocator, self).tick_values(vmin, vmax)
        return [bisect.bisect_left(self._dates, x) for x in dtnums]


class AutoDateLocator(ADLocator):

    def __init__(self, dates, *args, **kwargs):
        self._dates = dates
        super(AutoDateLocator, self).__init__(*args, **kwargs)

    def datalim_to_dt(self):
        """
        Convert axis data interval to datetime objects.
        """
        dmin, dmax = self.axis.get_data_interval()
        if dmin > dmax:
            dmin, dmax = dmax, dmin

        return (_idx2dt(dmin, self._dates, self.tz),
                _idx2dt(dmax, self._dates, self.tz))

    def viewlim_to_dt(self):
        """
        Converts the view interval to datetime objects.
        """
        vmin, vmax = self.axis.get_view_interval()
        if vmin > vmax:
            vmin, vmax = vmax, vmin

        return (_idx2dt(vmin, self._dates, self.tz),
                _idx2dt(vmax, self._dates, self.tz))

    def tick_values(self, vmin, vmax):
        import bisect
        dtnums = super(AutoDateLocator, self).tick_values(vmin, vmax)
        return [bisect.bisect_left(self._dates, x) for x in dtnums]

    def get_locator(self, dmin, dmax):
        '根据时间距离选择最佳 locator。'
        delta = relativedelta(dmax, dmin)
        tdelta = dmax - dmin

        # 使用绝对差值
        if dmin > dmax:
            delta = -delta
            tdelta = -tdelta

        # 下面混用 relativedelta 与 timedelta 方法，因为这些相似函数的能力不完全重叠；
        # 能复用库方法时避免自己实现日期数学。
        numYears = float(delta.years)
        numMonths = (numYears * MONTHS_PER_YEAR) + delta.months
        numDays = tdelta.days   # Avoids estimates of days/month, days/year
        numHours = (numDays * HOURS_PER_DAY) + delta.hours
        numMinutes = (numHours * MIN_PER_HOUR) + delta.minutes
        numSeconds = np.floor(tdelta.total_seconds())
        numMicroseconds = np.floor(tdelta.total_seconds() * 1e6)

        nums = [numYears, numMonths, numDays, numHours, numMinutes,
                numSeconds, numMicroseconds]

        use_rrule_locator = [True] * 6 + [False]

        # 传给 rrule 的 bymonth 等默认设置：
        # [unused（year）, bymonth, bymonthday, byhour, byminute,
        #  bysecond, unused（microseconds）]
        byranges = [None, 1, 1, 0, 0, 0, None]

        usemicro = False  # 作为 flag 使用，避免抛出异常

        # 遍历所有 frequency，找到至少能给出 minticks 个 tick position 的配置。
        # 找到后，再从该 frequency 对应列表中选择不超过 maxticks 的 interval。
        # 同时准备传给 rrulewrapper 的 bymonth 等 range。
        for i, (freq, num) in enumerate(zip(self._freqs, nums)):
            # 当前 frequency 不能给出足够 tick 时继续尝试下一种
            if num < self.minticks:
                # 未使用该 frequency 时，将对应 by_ 设为 None，便于 rrule 正确处理
                byranges[i] = None
                continue

            # 找到第一个不会产生过多 tick 的 interval
            for interval in self.intervald[freq]:
                if num <= interval * (self.maxticks[freq] - 1):
                    break
            else:
                # 遍历后仍未找到合适 interval，默认使用列表最后一个并发出 warning
                warnings.warn('AutoDateLocator was unable to pick an '
                              'appropriate interval for this date range. '
                              'It may be necessary to add an interval value '
                              "to the AutoDateLocator's intervald dictionary."
                              ' Defaulting to {0}.'.format(interval))

            # 设置相应参数
            self._freq = freq

            if self._byranges[i] and self.interval_multiples:
                byranges[i] = self._byranges[i][::interval]
                interval = 1
            else:
                byranges[i] = self._byranges[i]

            # 已找到要使用的 frequency
            break
        else:
            if False:
                raise ValueError(
                    'No sensible date limit could be found in the '
                    'AutoDateLocator.')
            else:
                usemicro = True

        if not usemicro and use_rrule_locator[i]:
            _, bymonth, bymonthday, byhour, byminute, bysecond, _ = byranges

            rrule = rrulewrapper(self._freq, interval=interval,
                                 dtstart=dmin, until=dmax,
                                 bymonth=bymonth, bymonthday=bymonthday,
                                 byhour=byhour, byminute=byminute,
                                 bysecond=bysecond)

            locator = RRuleLocator(self._dates, rrule, self.tz)
        else:
            if usemicro:
                interval = 1  # 因为进入 for else，尚未设置 interval
            locator = MicrosecondLocator(interval, tz=self.tz)

        locator.set_axis(self.axis)

        try:
            # 尝试兼容 matplotlib < 3.6.0
            locator.set_view_interval(*self.axis.get_view_interval())
            locator.set_data_interval(*self.axis.get_data_interval())
        except Exception as e:
            try:
                # 尝试兼容 matplotlib >= 3.6.0
                self.axis.set_view_interval(*self.axis.get_view_interval())
                self.axis.set_data_interval(*self.axis.get_data_interval())
                locator.set_axis(self.axis)
            except Exception as e:
                print("Error:", e)

        return locator


class AutoDateFormatter(ADFormatter):
    def __init__(self, dates, locator, tz=None, defaultfmt='%Y-%m-%d'):
        self._dates = dates
        super(AutoDateFormatter, self).__init__(locator, tz, defaultfmt)

    def __call__(self, x, pos=None):
        '''返回 ``pos`` 位置上 time ``x`` 的 label。'''
        x = int(round(x))
        ldates = len(self._dates)
        if x >= ldates:
            x = ldates - 1

        if x < 0:
            x = 0

        ix = self._dates[x]

        return super(AutoDateFormatter, self).__call__(ix, pos)
