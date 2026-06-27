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


from datetime import datetime, date, timedelta

from .dataseries import TimeFrame, _Bar
from .utils.py3 import with_metaclass
from . import metabase
from .utils.date import date2num, num2date


class DTFaker(object):
    '''datetime 代理对象，用于 resampler 在 data 未推进时执行时间检查。'''

    # 仅用于某些 data source：它们会在某些时刻从 _load 返回 None，
    # 表示需要检查 resampler 和/或 notification queue。
    # 这最初面向 real-time feed，因为这类 feed 需要上述 event。
    # 这些 data source 也应直接产出 ``utc`` 时间，因为 real-time feed 通常带 timestamp，
    # 而 utc 可提供通用参考。
    # 因此下面选择 UTC timestamp 并直接传给 date2num，以避免 localization。
    # 但 datetime object 仍从 data.num2date 提取，以确保返回值按用户期望输出
    # （本地 timezone 或指定 timezone）完成 localized。

    def __init__(self, data, forcedata=None):
        self.data = data

        # 别名
        self.datetime = self
        self.p = self

        if forcedata is None:
            _dtime = datetime.utcnow() + data._timeoffset()
            self._dt = dt = date2num(_dtime)  # utc-like time
            self._dtime = data.num2date(dt)  # localized time
        else:
            self._dt = forcedata.datetime[0]  # utc-like time
            self._dtime = forcedata.datetime.datetime()  # localized time

        self.sessionend = data.p.sessionend

    def __len__(self):
        return len(self.data)

    def __call__(self, idx=0):
        return self._dtime  # 模拟 data.datetime.datetime()

    def datetime(self, idx=0):
        return self._dtime

    def date(self, idx=0):
        return self._dtime.date()

    def time(self, idx=0):
        return self._dtime.time()

    @property
    def _calendar(self):
        return self.data._calendar

    def __getitem__(self, idx):
        return self._dt if idx == 0 else float('-inf')

    def num2date(self, *args, **kwargs):
        return self.data.num2date(*args, **kwargs)

    def date2num(self, *args, **kwargs):
        return self.data.date2num(*args, **kwargs)

    def _getnexteos(self):
        return self.data._getnexteos()


class _BaseResampler(with_metaclass(metabase.MetaParams, object)):
    '''Resampler/Replayer 的基类，用于处理时间边界、compression 和 bar 聚合。'''

    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', True),
        ('boundoff', 0),

        ('timeframe', TimeFrame.Days),
        ('compression', 1),

        ('takelate', True),

        ('sessionend', True),
    )

    def __init__(self, data):
        self.subdays = TimeFrame.Ticks < self.p.timeframe < TimeFrame.Days
        self.subweeks = self.p.timeframe < TimeFrame.Weeks
        self.componly = (not self.subdays and
                         data._timeframe == self.p.timeframe and
                         not (self.p.compression % data._compression))

        self.bar = _Bar(maxdate=True)  # bar holder
        self.compcount = 0  # 已产生 bar 的计数，用于控制 compression
        self._firstbar = True
        self.doadjusttime = (self.p.bar2edge and self.p.adjbartime and
                             self.subweeks)

        self._nexteos = None

        # 按自身参数修改 data 信息
        data.resampling = 1
        data.replaying = self.replaying
        data._timeframe = self.p.timeframe
        data._compression = self.p.compression

        self.data = data

    def _latedata(self, data):
        # new data 位于 position 0，尚未从 stream 中移除
        if not self.subdays:
            return False

        # 时间已交付
        return len(data) > 1 and data.datetime[0] <= data.datetime[-1]

    def _checkbarover(self, data, fromcheck=False, forcedata=None):
        chkdata = DTFaker(data, forcedata) if fromcheck else data

        isover = False
        if not self.componly and not self._barover(chkdata):
            return isover

        if self.subdays and self.p.bar2edge:
            isover = True
        elif not fromcheck:  # fromcheck doesn't increase compcount
            self.compcount += 1
            if not (self.compcount % self.p.compression):
                # 已跨过 boundary 且已有足够 bar 满足 compression，继续
                isover = True

        return isover

    def _barover(self, data):
        tframe = self.p.timeframe

        if tframe == TimeFrame.Ticks:
            # Ticks 已是最低层级
            return self.bar.isopen()

        elif tframe < TimeFrame.Days:
            return self._barover_subdays(data)

        elif tframe == TimeFrame.Days:
            return self._barover_days(data)

        elif tframe == TimeFrame.Weeks:
            return self._barover_weeks(data)

        elif tframe == TimeFrame.Months:
            return self._barover_months(data)

        elif tframe == TimeFrame.Years:
            return self._barover_years(data)

    def _eosset(self):
        if self._nexteos is None:
            self._nexteos, self._nextdteos = self.data._getnexteos()
            return

    def _eoscheck(self, data, seteos=True, exact=False):
        if seteos:
            self._eosset()

        equal = data.datetime[0] == self._nextdteos
        grter = data.datetime[0] > self._nextdteos

        if exact:
            ret = equal
        else:
            # 如果被比较 data 超过 endofsession，需要确认 resampled bar 已打开，
            # 且在该 session end 之前已有内容。可能遇到周末，直到周一才有数据交付。
            if grter:
                ret = (self.bar.isopen() and
                       self.bar.datetime <= self._nextdteos)
            else:
                ret = equal

        if ret:
            self._lasteos = self._nexteos
            self._lastdteos = self._nextdteos
            self._nexteos = None
            self._nextdteos = float('-inf')

        return ret

    def _barover_days(self, data):
        return self._eoscheck(data)

    def _barover_weeks(self, data):
        if self.data._calendar is None:
            year, week, _ = data.num2date(self.bar.datetime).date().isocalendar()
            yearweek = year * 100 + week

            baryear, barweek, _ = data.datetime.date().isocalendar()
            bar_yearweek = baryear * 100 + barweek

            return bar_yearweek > yearweek
        else:
            return data._calendar.last_weekday(data.datetime.date())

    def _barover_months(self, data):
        dt = data.num2date(self.bar.datetime).date()
        yearmonth = dt.year * 100 + dt.month

        bardt = data.datetime.datetime()
        bar_yearmonth = bardt.year * 100 + bardt.month

        return bar_yearmonth > yearmonth

    def _barover_years(self, data):
        return (data.datetime.datetime().year >
                data.num2date(self.bar.datetime).year)

    def _gettmpoint(self, tm):
        '''按 timeframe 返回给定 time 在日内对应的时间点。

          - 示例 1：00:05:00 按 minutes -> point = 5
          - 示例 2：00:05:20 按 seconds -> point = 5 * 60 + 20 = 320
        '''
        point = tm.hour * 60 + tm.minute
        restpoint = 0

        if self.p.timeframe < TimeFrame.Minutes:
            point = point * 60 + tm.second

            if self.p.timeframe < TimeFrame.Seconds:
                point = point * 1e6 + tm.microsecond
            else:
                restpoint = tm.microsecond
        else:
            restpoint = tm.second + tm.microsecond

        point += self.p.boundoff

        return point, restpoint

    def _barover_subdays(self, data):
        if self._eoscheck(data):
            return True

        if data.datetime[0] < self.bar.datetime:
            return False

        # 获取比较用 time object，采用 utc-like 格式
        tm = num2date(self.bar.datetime).time()
        bartm = num2date(data.datetime[0]).time()

        point, _ = self._gettmpoint(tm)
        barpoint, _ = self._gettmpoint(bartm)

        ret = False
        if barpoint > point:
            # data bar 已超过内部 bar
            if not self.p.bar2edge:
                # 按简单 bar 计数完成 compression（类似 days）
                ret = True
            elif self.p.compression == 1:
                # 未请求 bar compression，内部 bar 已完成
                ret = True
            else:
                point_comp = point // self.p.compression
                barpoint_comp = barpoint // self.p.compression

                # 已跨过包含 compression 的 boundary
                if barpoint_comp > point_comp:
                    ret = True

        return ret

    def check(self, data, _forcedata=None):
        '''检查当前已保存 bar 是否应在 data 未推进时交付。

        如果 live feed 没有新 tick 进入，一个 5 秒 resampled bar 可能会在 20 秒后才交付。
        调用该方法时，会使用 wall clock（包含 data time offset）检查时间是否已经推进到
        必须交付已保存 data 的程度。
        '''
        if not self.bar.isopen():
            return

        return self(data, fromcheck=True, forcedata=_forcedata)

    def _dataonedge(self, data):
        if not self.subweeks:
            if data._calendar is None:
                return False, True  # nothing can be done

            tframe = self.p.timeframe
            ret = False
            if tframe == TimeFrame.Weeks:  # Ticks 已是最低层级
                ret = data._calendar.last_weekday(data.datetime.date())
            elif tframe == TimeFrame.Months:
                ret = data._calendar.last_monthday(data.datetime.date())
            elif tframe == TimeFrame.Years:
                ret = data._calendar.last_yearday(data.datetime.date())

            if ret:
                # Data 必须被消费，但 compression 可能尚未满足。
                # 防止调用 barcheckover，因为它可能再次增加 compcount。
                docheckover = False
                self.compcount += 1
                ret = not (self.compcount % self.p.compression)
            else:
                docheckover = True

            return ret, docheckover

        if self._eoscheck(data, exact=True):
            return True, True

        if self.subdays:
            point, prest = self._gettmpoint(data.datetime.time())
            if prest:
                return False, True  # 存在 subunits，不可能在 boundary 上

            # 通过 compression 获取 boundary 和超出 boundary 的余数
            bound, brest = divmod(point, self.p.compression)

            # 没有额外余数且 decomp 后 boundary 等于 point
            return (brest == 0 and point == (bound * self.p.compression), True)

        # 由 eoscheck 覆盖的代码
        if False and self.p.sessionend:
            # Days 场景：在输出 timezone 中获取 datetime 进行比较，
            # 因为 p.sessionend 预期位于输出 timezone。
            bdtime = data.datetime.datetime()
            bsend = datetime.combine(bdtime.date(), data.p.sessionend)
            return bdtime == bsend

        return False, True  # subweeks，但不是 subdays，也不是 sessionend

    def _calcadjtime(self, greater=False):
        if self._nexteos is None:
            # Session 已超过，使用 end of session 作为标记
            return self._lastdteos  # utc-like

        dt = self.data.num2date(self.bar.datetime)

        # 获取当前 time
        tm = dt.time()
        # 获取当天在 timeframe 单位上的 point（例如 minute 200）
        point, _ = self._gettmpoint(tm)

        # 应用 compression 更新 point 位置（comp 5 -> 200 // 5）
        # point = (point // self.p.compression)
        point = point // self.p.compression

        # 如果启用 rightedge（boundary end），除递归场景外加上它
        point += self.p.rightedge

        # 反向应用 compression，将 point 恢复为 timeframe 单位
        point *= self.p.compression

        # 获取 hours、minutes、seconds 和 microseconds
        extradays = 0
        if self.p.timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self.p.timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self.p.timeframe <= TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)
        elif self.p.timeframe == TimeFrame.Days:
            # 最后兜底
            eost = self._nexteos.time()
            ph = eost.hour
            pm = eost.minute
            ps = eost.second
            pus = eost.microsecond

        if ph > 23:  # 跨过午夜
            extradays = ph // 24
            ph %= 24

        # 用计算结果替换日内部分并更新
        dt = dt.replace(hour=int(ph), minute=int(pm),
                        second=int(ps), microsecond=int(pus))
        if extradays:
            dt += timedelta(days=extradays)
        dtnum = self.data.date2num(dt)
        return dtnum

    def _adjusttime(self, greater=False, forcedata=None):
        '''调整已计算 bar 的时间。

        该方法根据 timeframe 和 compression，把底层 data source 得出的 bar 时间调整到
        合适 boundary。根据参数 ``rightedge``，使用起始 boundary 或结束 boundary。
        '''
        dtnum = self._calcadjtime(greater=greater)
        if greater and dtnum <= self.bar.datetime:
            return False

        self.bar.datetime = dtnum
        return True


class Resampler(_BaseResampler):
    '''将给定 timeframe 的 data resample 到更大 timeframe。

    Args:

      - ``bar2edge`` (default: ``True``)

        使用时间 boundary 作为 resample 目标。例如 "ticks -> 5 seconds" 时，
        生成的 5 秒 bar 会对齐到 xx:00、xx:05、xx:10 ...

      - ``adjbartime`` (default: ``True``)

        使用 boundary 时间调整交付的 resampled bar 时间，而不是使用最后看到的
        timestamp。例如 resample 到 "5 seconds" 时，即使最后看到的 timestamp 是
        hh:mm:04.33，bar 时间也会被调整到 hh:mm:05。

        .. note::

           只有 "bar2edge" 为 True 时才会调整时间。如果 bar 未对齐到 boundary，
           调整时间没有意义。

      - ``rightedge`` (default: ``True``)

        使用时间 boundary 的右边界来设置时间。

        如果为 ``False`` 且压缩到 5 秒，则 hh:mm:00 到 hh:mm:04 之间生成的
        resampled bar 时间会是 hh:mm:00（起始 boundary）。

        如果为 ``True``，用于时间的 boundary 会是 hh:mm:05（结束 boundary）。

    Returns:
        Resampler: 将输入 data 聚合为更大 timeframe bar 的 filter。
    '''
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', True),
    )

    replaying = False

    def last(self, data):
        '''当 data 不再产生 bar 时调用。

        该方法可能被多次调用。它可以用于生成仍在累计、尚需交付的额外 bar。
        '''
        if self.bar.isopen():
            if self.doadjusttime:
                self._adjusttime()

            data._add2stack(self.bar.lvalues())
            self.bar.bstart(maxdate=True)  # 关闭 bar，避免重复
            return True

        return False

    def __call__(self, data, fromcheck=False, forcedata=None):
        '''对 data source 产生的每组 value 调用。'''
        consumed = False
        onedge = False
        docheckover = True
        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards()
                    return True  # 获取 new bar

                self.bar.bupdate(data)  # 更新 new 或 existing bar
                # 将时间推到 reference 之后
                self.bar.datetime = data.datetime[-1] + 0.000001
                data.backwards()  # 移除已用 bar
                return True

            if self.componly:  # 仅在非 subdays 时
                # rewinding 前获取 session ref
                _, self._lastdteos = self.data._getnexteos()
                consumed = True

            else:
                onedge, docheckover = self._dataonedge(data)  # 用于 subdays
                consumed = onedge

        if consumed:
            self.bar.bupdate(data)  # 更新 new 或 existing bar
            data.backwards()  # 移除已用 bar

        # if self.bar.isopen and (onedge or (docheckover and checkbarover))
        cond = self.bar.isopen()
        if cond:  # 原始逻辑是 and，第二项也必须为 true
            if not onedge:  # onedge 为 true 已足够
                if docheckover:
                    cond = self._checkbarover(data, fromcheck=fromcheck,
                                              forcedata=forcedata)
        if cond:
            dodeliver = False
            if forcedata is not None:
                # 检查交付时间不能大于 forcedata 的时间
                tframe = self.p.timeframe
                if tframe == TimeFrame.Ticks:  # Ticks 已是最低层级
                    dodeliver = True
                elif tframe == TimeFrame.Minutes:
                    dtnum = self._calcadjtime(greater=True)
                    dodeliver = dtnum <= forcedata.datetime[0]
                elif tframe == TimeFrame.Days:
                    dtnum = self._calcadjtime(greater=True)
                    dodeliver = dtnum <= forcedata.datetime[0]
            else:
                dodeliver = True

            if dodeliver:
                if not onedge and self.doadjusttime:
                    self._adjusttime(greater=True, forcedata=forcedata)

                data._add2stack(self.bar.lvalues())
                self.bar.bstart(maxdate=True)  # bar 已交付 -> restart

        if not fromcheck:
            if not consumed:
                self.bar.bupdate(data)  # 更新 new 或 existing bar
                data.backwards()  # 移除已用 bar

        return True


class Replayer(_BaseResampler):
    '''将给定 timeframe 的 data replay 到更大 timeframe。

    它会用 tick/seconds/minutes data 逐步构建更大 bar（例如 daily bar），以模拟
    市场实时形成 bar 的过程。

    只有 bar 完成时，data 的 "length" 才会真正变化，从而交付一个 closed bar。

    Args:

      - ``bar2edge`` (default: ``True``)

        使用时间 boundary 作为 closed bar 的目标。例如 "ticks -> 5 seconds" 时，
        生成的 5 秒 bar 会对齐到 xx:00、xx:05、xx:10 ...

      - ``adjbartime`` (default: ``False``)

        使用 boundary 时间调整交付的 resampled bar 时间，而不是使用最后看到的
        timestamp。例如 resample 到 "5 seconds" 时，即使最后看到的 timestamp 是
        hh:mm:04.33，bar 时间也会被调整到 hh:mm:05。

        .. note::

           只有 "bar2edge" 为 True 时才会调整时间。如果 bar 未对齐到 boundary，
           调整时间没有意义。

        .. note:: 如果该参数为 True，会在 *replayed* bar 末尾引入一个带 *adjusted*
                  time 的额外 tick。

      - ``rightedge`` (default: ``True``)

        使用时间 boundary 的右边界来设置时间。

        如果为 ``False`` 且压缩到 5 秒，则 hh:mm:00 到 hh:mm:04 之间生成的
        resampled bar 时间会是 hh:mm:00（起始 boundary）。

        如果为 ``True``，用于时间的 boundary 会是 hh:mm:05（结束 boundary）。

    Returns:
        Replayer: 逐步构造更大 timeframe bar 的 replay filter。
    '''
    params = (
        ('bar2edge', True),
        ('adjbartime', False),
        ('rightedge', True),
    )

    replaying = True

    def __call__(self, data, fromcheck=False, forcedata=None):
        consumed = False
        onedge = False
        takinglate = False
        docheckover = True

        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards(force=True)
                    return True  # 获取 new bar

                consumed = True
                takinglate = True

            elif self.componly:  # 仅在非 subdays 时
                consumed = True

            else:
                onedge, docheckover = self._dataonedge(data)  # 用于 subdays
                consumed = onedge

            data._tick_fill(force=True)  # 更新

        if consumed:
            self.bar.bupdate(data)
            if takinglate:
                self.bar.datetime = data.datetime[-1] + 0.000001

        # if onedge or (checkbarover and self._checkbarover)
        cond = onedge
        if not cond:  # 原始逻辑是 or，若为 true 即可满足
            if docheckover:
                cond = self._checkbarover(data, fromcheck=fromcheck)
        if cond:
            if not onedge and self.doadjusttime:  # 插入带 adjtime 的 tick
                adjusted = self._adjusttime(greater=True)
                if adjusted:
                    ago = 0 if (consumed or fromcheck) else -1
                    # 更新到 new data 之前的那个点
                    data._updatebar(self.bar.lvalues(), forward=False, ago=ago)

                if not fromcheck:
                    if not consumed:
                        # 用真实 new data 重新打开 bar，并把 data 保存到 queue
                        self.bar.bupdate(data, reopen=True)
                        # erase 为 True，但 tick 不会在下面被看到，因此无需标记为第 1 个
                        data._save2stack(erase=True, force=True)
                    else:
                        self.bar.bstart(maxdate=True)
                        self._firstbar = True  # next 是 first
                else:  # from check
                    # fromcheck 或 consumed 已强制交付，重新打开
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  # next 是 first
                    if adjusted:
                        # 如果这是 check，调整后需要重新交付
                        data._save2stack(erase=True, force=True)

            elif not fromcheck:
                if not consumed:
                    # Data 已经 "forwarded"，并且 replay 到 new bar。
                    # 无需 backwards，直接重新打开内部 cache。
                    self.bar.bupdate(data, reopen=True)
                else:
                    # 仅 compression：已用 data 更新 bar，因此从 stream 中移除，
                    # 更新 existing data，并重新打开 bar。
                    if not self._firstbar:  # 仅在不是 firstbar 时丢弃 data
                        data.backwards(force=True)
                    data._updatebar(self.bar.lvalues(), forward=False, ago=0)
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  # 确保 next tick 向前推进

        elif not fromcheck:
            # 尚未结束：更新、移除 new entry、交付
            if not consumed:
                self.bar.bupdate(data)

            if not self._firstbar:  # 仅在不是 firstbar 时丢弃 data
                data.backwards(force=True)

            data._updatebar(self.bar.lvalues(), forward=False, ago=0)
            self._firstbar = False

        return False  # existing bar 可由系统处理


class ResamplerTicks(Resampler):
    params = (('timeframe', TimeFrame.Ticks),)


class ResamplerSeconds(Resampler):
    params = (('timeframe', TimeFrame.Seconds),)


class ResamplerMinutes(Resampler):
    params = (('timeframe', TimeFrame.Minutes),)


class ResamplerDaily(Resampler):
    params = (('timeframe', TimeFrame.Days),)


class ResamplerWeekly(Resampler):
    params = (('timeframe', TimeFrame.Weeks),)


class ResamplerMonthly(Resampler):
    params = (('timeframe', TimeFrame.Months),)


class ResamplerYearly(Resampler):
    params = (('timeframe', TimeFrame.Years),)


class ReplayerTicks(Replayer):
    params = (('timeframe', TimeFrame.Ticks),)


class ReplayerSeconds(Replayer):
    params = (('timeframe', TimeFrame.Seconds),)


class ReplayerMinutes(Replayer):
    params = (('timeframe', TimeFrame.Minutes),)


class ReplayerDaily(Replayer):
    params = (('timeframe', TimeFrame.Days),)


class ReplayerWeekly(Replayer):
    params = (('timeframe', TimeFrame.Weeks),)


class ReplayerMonthly(Replayer):
    params = (('timeframe', TimeFrame.Months),)
