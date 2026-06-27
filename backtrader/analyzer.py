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

import calendar
from collections import OrderedDict
import datetime
import pprint as pp

import backtrader as bt
from backtrader import TimeFrame
from backtrader.utils.py3 import MAXINT, with_metaclass


class MetaAnalyzer(bt.MetaParams):
    def donew(cls, *args, **kwargs):
        '''
        拦截 strategy 参数。
        '''
        # 创建对象并设置 params
        _obj, args, kwargs = super(MetaAnalyzer, cls).donew(*args, **kwargs)

        _obj._children = list()

        _obj.strategy = strategy = bt.metabase.findowner(_obj, bt.Strategy)
        _obj._parent = bt.metabase.findowner(_obj, Analyzer)

        # 如果在 master observer 内创建，则向其注册
        masterobs = bt.metabase.findowner(_obj, bt.Observer)
        if masterobs is not None:
            masterobs._register_analyzer(_obj)

        _obj.datas = strategy.datas

        # 为每个 data 添加 alias：第一个 data 同时是 data 和 data0
        if _obj.datas:
            _obj.data = data = _obj.datas[0]

            for l, line in enumerate(data.lines):
                linealias = data._getlinealias(l)
                if linealias:
                    setattr(_obj, 'data_%s' % linealias, line)
                setattr(_obj, 'data_%d' % l, line)

            for d, data in enumerate(_obj.datas):
                setattr(_obj, 'data%d' % d, data)

                for l, line in enumerate(data.lines):
                    linealias = data._getlinealias(l)
                    if linealias:
                        setattr(_obj, 'data%d_%s' % (d, linealias), line)
                    setattr(_obj, 'data%d_%d' % (d, l), line)

        _obj.create_analysis()

        # 回到正常调用链
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAnalyzer, cls).dopostinit(_obj, *args, **kwargs)

        if _obj._parent is not None:
            _obj._parent._register(_obj)

        # 回到正常调用链
        return _obj, args, kwargs


class Analyzer(with_metaclass(MetaAnalyzer, object)):
    '''Analyzer 的基类，用于在 strategy 运行过程中收集并返回分析结果。

    Analyzer 实例在 strategy 的上下文中运行，并为该 strategy 提供分析结果。

    自动设置的成员属性:

      - ``self.strategy``: 访问 *strategy* 以及 strategy 可访问的所有内容

      - ``self.datas[x]``: 访问系统中的 data feeds 数组，也可通过 strategy
        引用访问

      - ``self.data``: 访问 ``self.datas[0]``

      - ``self.dataX`` -> ``self.datas[X]``

      - ``self.dataX_Y`` -> ``self.datas[X].lines[Y]``

      - ``self.dataX_name`` -> ``self.datas[X].name``

      - ``self.data_name`` -> ``self.datas[0].name``

      - ``self.data_Y`` -> ``self.datas[0].lines[Y]``

    Analyzer 不是 *Lines* 对象，但方法和运行方式遵循相同设计:

      - ``__init__``: 实例化和初始设置阶段调用

      - ``start`` / ``stop``: 标记运行开始和结束

      - ``prenext`` / ``nextstart`` / ``next``: 跟随 strategy 中同名方法的调用

      - ``notify_trade`` / ``notify_order`` / ``notify_cashvalue`` /
        ``notify_fund``: 接收与 strategy 中同名方法相同的通知

    Analyzer 的运行模式是开放的，不强制某一种模式。因此分析结果既可以在
    ``next`` 调用中生成，也可以在运行结束时的 ``stop`` 中生成，甚至可以只用
    ``notify_trade`` 这类单个方法生成。

    子类最重要的是覆盖 ``get_analysis``，返回包含分析结果的 *dict-like*
    对象。实际格式由具体实现决定。

    '''
    csv = True

    def __len__(self):
        '''支持对 analyzer 调用 ``len``。

        Returns:
            int: analyzer 所属 strategy 的当前长度。
        '''
        return len(self.strategy)

    def _register(self, child):
        self._children.append(child)

    def _prenext(self):
        for child in self._children:
            child._prenext()

        self.prenext()

    def _notify_cashvalue(self, cash, value):
        for child in self._children:
            child._notify_cashvalue(cash, value)

        self.notify_cashvalue(cash, value)

    def _notify_fund(self, cash, value, fundvalue, shares):
        for child in self._children:
            child._notify_fund(cash, value, fundvalue, shares)

        self.notify_fund(cash, value, fundvalue, shares)

    def _notify_trade(self, trade):
        for child in self._children:
            child._notify_trade(trade)

        self.notify_trade(trade)

    def _notify_order(self, order):
        for child in self._children:
            child._notify_order(order)

        self.notify_order(order)

    def _nextstart(self):
        for child in self._children:
            child._nextstart()

        self.nextstart()

    def _next(self):
        for child in self._children:
            child._next()

        self.next()

    def _start(self):
        for child in self._children:
            child._start()

        self.start()

    def _stop(self):
        for child in self._children:
            child._stop()

        self.stop()

    def notify_cashvalue(self, cash, value):
        '''在每个 next cycle 前接收 cash/value 通知。

        Args:
            cash (float): 当前 cash。
            value (float): 当前 portfolio value。
        '''
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        '''接收当前 cash、value、fundvalue 和 fund shares。

        Args:
            cash (float): 当前 cash。
            value (float): 当前 portfolio value。
            fundvalue (float): 当前 fund value。
            shares (float): 当前 fund shares。
        '''
        pass

    def notify_order(self, order):
        '''在每个 next cycle 前接收 order 通知。

        Args:
            order: 发生状态变化的 order。
        '''
        pass

    def notify_trade(self, trade):
        '''在每个 next cycle 前接收 trade 通知。

        Args:
            trade: 发生状态变化的 trade。
        '''
        pass

    def next(self):
        '''当 strategy 达到最小 period 后，随 strategy 的每次 next 调用而调用。'''
        pass

    def prenext(self):
        '''在 strategy 达到最小 period 前，随 strategy 的每次 prenext 调用而调用。

        默认行为是调用 ``next``。
        '''
        self.next()

    def nextstart(self):
        '''当 strategy 首次达到最小 period 时，随 strategy 的 nextstart 调用一次。
        '''
        self.next()

    def start(self):
        '''运行开始时调用，用于让 analyzer 设置所需状态。'''
        pass

    def stop(self):
        '''运行结束时调用，用于让 analyzer 收尾或生成最终结果。'''
        pass

    def create_analysis(self):
        '''供子类覆盖，用于创建保存分析结果的数据结构。

        默认行为是创建名为 ``rets`` 的 ``OrderedDict``。
        '''
        self.rets = OrderedDict()

    def get_analysis(self):
        '''返回包含分析结果的 *dict-like* 对象。

        Returns:
            dict-like: 分析结果。key 和结果格式由具体实现决定。

        这里并不强制返回值一定是 *dict-like object*，这只是约定。默认实现返回
        由默认 ``create_analysis`` 方法创建的 ``OrderedDict`` ``rets``。

        '''
        return self.rets

    def print(self, *args, **kwargs):
        '''通过标准 ``WriterFile`` 对象打印 ``get_analysis`` 返回的结果。

        Args:
            *args: 传给 ``WriterFile`` 的位置参数。
            **kwargs: 传给 ``WriterFile`` 的关键字参数。

        默认会写到 standard output。
        '''
        writer = bt.WriterFile(*args, **kwargs)
        writer.start()
        pdct = dict()
        pdct[self.__class__.__name__] = self.get_analysis()
        writer.writedict(pdct)
        writer.stop()

    def pprint(self, *args, **kwargs):
        '''使用 Python 的 pretty print 模块（*pprint*）打印分析结果。

        Args:
            *args: 传给 ``pprint`` 的位置参数。
            **kwargs: 传给 ``pprint`` 的关键字参数。
        '''
        pp.pprint(self.get_analysis(), *args, **kwargs)


class MetaTimeFrameAnalyzerBase(Analyzer.__class__):
    def __new__(meta, name, bases, dct):
        # Hack to support original method name
        if '_on_dt_over' in dct:
            dct['on_dt_over'] = dct.pop('_on_dt_over')  # rename method

        return super(MetaTimeFrameAnalyzerBase, meta).__new__(meta, name,
                                                              bases, dct)


class TimeFrameAnalyzerBase(with_metaclass(MetaTimeFrameAnalyzerBase,
                                           Analyzer)):
    params = (
        ('timeframe', None),
        ('compression', None),
        ('_doprenext', True),
    )

    def _start(self):
        # Override to add specific attributes
        self.timeframe = self.p.timeframe or self.data._timeframe
        self.compression = self.p.compression or self.data._compression

        self.dtcmp, self.dtkey = self._get_dt_cmpkey(datetime.datetime.min)
        super(TimeFrameAnalyzerBase, self)._start()

    def _prenext(self):
        for child in self._children:
            child._prenext()

        if self._dt_over():
            self.on_dt_over()

        if self.p._doprenext:
            self.prenext()

    def _nextstart(self):
        for child in self._children:
            child._nextstart()

        if self._dt_over() or not self.p._doprenext:  # exec if no prenext
            self.on_dt_over()

        self.nextstart()

    def _next(self):
        for child in self._children:
            child._next()

        if self._dt_over():
            self.on_dt_over()

        self.next()

    def on_dt_over(self):
        pass

    def _dt_over(self):
        if self.timeframe == TimeFrame.NoTimeFrame:
            dtcmp, dtkey = MAXINT, datetime.datetime.max
        else:
            # With >= 1.9.x the system datetime is in the strategy
            dt = self.strategy.datetime.datetime()
            dtcmp, dtkey = self._get_dt_cmpkey(dt)

        if self.dtcmp is None or dtcmp > self.dtcmp:
            self.dtkey, self.dtkey1 = dtkey, self.dtkey
            self.dtcmp, self.dtcmp1 = dtcmp, self.dtcmp
            return True

        return False

    def _get_dt_cmpkey(self, dt):
        if self.timeframe == TimeFrame.NoTimeFrame:
            return None, None

        if self.timeframe == TimeFrame.Years:
            dtcmp = dt.year
            dtkey = datetime.date(dt.year, 12, 31)

        elif self.timeframe == TimeFrame.Months:
            dtcmp = dt.year * 100 + dt.month
            _, lastday = calendar.monthrange(dt.year, dt.month)
            dtkey = datetime.datetime(dt.year, dt.month, lastday)

        elif self.timeframe == TimeFrame.Weeks:
            isoyear, isoweek, isoweekday = dt.isocalendar()
            dtcmp = isoyear * 100 + isoweek
            sunday = dt + datetime.timedelta(days=7 - isoweekday)
            dtkey = datetime.datetime(sunday.year, sunday.month, sunday.day)

        elif self.timeframe == TimeFrame.Days:
            dtcmp = dt.year * 10000 + dt.month * 100 + dt.day
            dtkey = datetime.datetime(dt.year, dt.month, dt.day)

        else:
            dtcmp, dtkey = self._get_subday_cmpkey(dt)

        return dtcmp, dtkey

    def _get_subday_cmpkey(self, dt):
        # Calculate intraday position
        point = dt.hour * 60 + dt.minute

        if self.timeframe < TimeFrame.Minutes:
            point = point * 60 + dt.second

        if self.timeframe < TimeFrame.Seconds:
            point = point * 1e6 + dt.microsecond

        # Apply compression to update point position (comp 5 -> 200 // 5)
        point = point // self.compression

        # Move to next boundary
        point += 1

        # Restore point to the timeframe units by de-applying compression
        point *= self.compression

        # Get hours, minutes, seconds and microseconds
        if self.timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self.timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self.timeframe == TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)

        extradays = 0
        if ph > 23:  # went over midnight:
            extradays = ph // 24
            ph %= 24

        # moving 1 minor unit to the left to be in the boundary
        # pm -= self.timeframe == TimeFrame.Minutes
        # ps -= self.timeframe == TimeFrame.Seconds
        # pus -= self.timeframe == TimeFrame.MicroSeconds

        tadjust = datetime.timedelta(
            minutes=self.timeframe == TimeFrame.Minutes,
            seconds=self.timeframe == TimeFrame.Seconds,
            microseconds=self.timeframe == TimeFrame.MicroSeconds)

        # Add extra day if present
        if extradays:
            dt += datetime.timedelta(days=extradays)

        # Replace intraday parts with the calculated ones and update it
        dtcmp = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)
        dtcmp -= tadjust
        dtkey = dtcmp

        return dtcmp, dtkey
