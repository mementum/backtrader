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

import collections
import operator
import sys

from .utils.py3 import map, range, zip, with_metaclass, string_types
from .utils import DotDict

from .lineroot import LineRoot, LineSingle
from .linebuffer import LineActions, LineNum
from .lineseries import LineSeries, LineSeriesMaker
from .dataseries import DataSeries
from . import metabase


class MetaLineIterator(LineSeries.__class__):
    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineIterator, cls).donew(*args, **kwargs)

        # 准备用于保存需要计算、且会影响 minperiod 的子对象
        # 放在这里是为了支持下面的 LineNum
        _obj._lineiterators = collections.defaultdict(list)

        # 扫描 args 中的 data；如果没有找到，则使用 _owner 作为 clock
        mindatas = _obj._mindatas
        lastarg = 0
        _obj.datas = []
        for arg in args:
            if isinstance(arg, LineRoot):
                _obj.datas.append(LineSeriesMaker(arg))

            elif not mindatas:
                break  # 找到非 data，且不需要继续收集
            else:
                try:
                    _obj.datas.append(LineSeriesMaker(LineNum(arg)))
                except:
                    # 既不是 LineNum，也不是 LineSeries，退出扫描
                    break

            mindatas = max(0, mindatas - 1)
            lastarg += 1

        newargs = args[lastarg:]

        # 如果 indicator 没有传入 data，则使用 owner 的主 data，方便直接写 self.data
        if not _obj.datas and isinstance(_obj, (IndicatorBase, ObserverBase)):
            _obj.datas = _obj._owner.datas[0:mindatas]

        # 创建字典以便检查对象是否存在。Python list 的 in 会使用 "==" 判断，
        # 实际检查的是相等而不是对象存在性。
        _obj.ddatas = {x: None for x in _obj.datas}

        # 为每个找到的 data 添加访问成员；第一个 data 同时拥有 data 和 data0
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

        # 参数值此时已经在 __init__ 前设置完毕
        _obj.dnames = DotDict([(d._name, d)
                               for d in _obj.datas if getattr(d, '_name', '')])

        return _obj, newargs, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineIterator, cls).dopreinit(_obj, *args, **kwargs)

        # 如果没有找到 data，则使用 _owner 作为 clock
        _obj.datas = _obj.datas or [_obj._owner]

        # 第一个 data source 是当前对象的 ticking clock
        _obj._clock = _obj.datas[0]

        # 通过扫描找到的 data 自动设置 period 起点。所有 data 都产出值之前不能计算。
        # data 本身也可能是 indicator，并且可能需要若干 bar 才能产出值。
        _obj._minperiod = \
            max([x._minperiod for x in _obj.datas] or [_obj._minperiod])

        # line 至少要携带与 data 相同的 minperiod
        for line in _obj.lines:
            line.addminperiod(_obj._minperiod)

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineIterator, cls).dopostinit(_obj, *args, **kwargs)

        # 自身 minperiod 至少等于所有 line 的最大 minperiod
        _obj._minperiod = max([x._minperiod for x in _obj.lines])

        # 重新计算 period
        _obj._periodrecalc()

        # _minperiod 计算完成后，把自身注册到 owner
        if _obj._owner is not None:
            _obj._owner.addindicator(_obj)

        return _obj, args, kwargs


class LineIterator(with_metaclass(MetaLineIterator, LineSeries)):
    '''line iterator 的基类，用于调度 data、indicator、observer 的 next/once 生命周期。'''

    _nextforce = False  # 强制 cerebro 使用 next 模式（runonce=False）

    _mindatas = 1
    _ltype = LineSeries.IndType

    plotinfo = dict(plot=True,
                    subplot=True,
                    plotname='',
                    plotskip=False,
                    plotabove=False,
                    plotlinelabels=False,
                    plotlinevalues=True,
                    plotvaluetags=True,
                    plotymargin=0.0,
                    plotyhlines=[],
                    plotyticks=[],
                    plothlines=[],
                    plotforce=False,
                    plotmaster=None,)

    def _periodrecalc(self):
        # 最后检查一次，防止部分 lineiterator 没有被直接或间接分配到 line
        # 典型例子是 Kaufman's Adaptive Moving Average
        indicators = self._lineiterators[LineIterator.IndType]
        indperiods = [ind._minperiod for ind in indicators]
        indminperiod = max(indperiods or [self._minperiod])
        self.updateminperiod(indminperiod)

    def _stage2(self):
        super(LineIterator, self)._stage2()

        for data in self.datas:
            data._stage2()

        for lineiterators in self._lineiterators.values():
            for lineiterator in lineiterators:
                lineiterator._stage2()

    def _stage1(self):
        super(LineIterator, self)._stage1()

        for data in self.datas:
            data._stage1()

        for lineiterators in self._lineiterators.values():
            for lineiterator in lineiterators:
                lineiterator._stage1()

    def getindicators(self):
        return self._lineiterators[LineIterator.IndType]

    def getindicators_lines(self):
        return [x for x in self._lineiterators[LineIterator.IndType]
                if hasattr(x.lines, 'getlinealiases')]

    def getobservers(self):
        return self._lineiterators[LineIterator.ObsType]

    def addindicator(self, indicator):
        # 存入对应队列
        self._lineiterators[indicator._ltype].append(indicator)

        # 使用 getattr，因为 line buffer 没有该属性
        if getattr(indicator, '_nextforce', False):
            # 该 indicator 需要 runonce=False
            o = self
            while o is not None:
                if o._ltype == LineIterator.StratType:
                    o.cerebro._disable_runonce()
                    break

                o = o._owner  # 沿层级向上移动

    def bindlines(self, owner=None, own=None):
        if not owner:
            owner = 0

        if isinstance(owner, string_types):
            owner = [owner]
        elif not isinstance(owner, collections.Iterable):
            owner = [owner]

        if not own:
            own = range(len(owner))

        if isinstance(own, string_types):
            own = [own]
        elif not isinstance(own, collections.Iterable):
            own = [own]

        for lineowner, lineown in zip(owner, own):
            if isinstance(lineowner, string_types):
                lownerref = getattr(self._owner.lines, lineowner)
            else:
                lownerref = self._owner.lines[lineowner]

            if isinstance(lineown, string_types):
                lownref = getattr(self.lines, lineown)
            else:
                lownref = self.lines[lineown]

            lownref.addbinding(lownerref)

        return self

    # 可读性更好的别名
    bind2lines = bindlines
    bind2line = bind2lines

    def _next(self):
        clock_len = self._clk_update()

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator._next()

        self._notify()

        if self._ltype == LineIterator.StratType:
            # 支持不同长度的 data
            minperstatus = self._getminperstatus()
            if minperstatus < 0:
                self.next()
            elif minperstatus == 0:
                self.nextstart()  # 只在第 1 个完整值时调用
            else:
                self.prenext()
        else:
            # 假定 indicator 等对象运行在同长度 data 上；上面的逻辑也可以泛化到这里
            if clock_len > self._minperiod:
                self.next()
            elif clock_len == self._minperiod:
                self.nextstart()  # 只在第 1 个完整值时调用
            elif clock_len:
                self.prenext()

    def _clk_update(self):
        clock_len = len(self._clock)
        if clock_len != len(self):
            self.forward()

        return clock_len

    def _once(self):
        self.forward(size=self._clock.buflen())

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator._once()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.forward(size=self.buflen())

        for data in self.datas:
            data.home()

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator.home()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.home()

        self.home()

        # 对 strategy 而言这 3 个方法保持为空，因此不起作用；strategy 总是按 next 执行。
        # indicator 则会按各自 minperiod 调用。
        self.preonce(0, self._minperiod - 1)
        self.oncestart(self._minperiod - 1, self._minperiod)
        self.once(self._minperiod, self.buflen())

        for line in self.lines:
            line.oncebinding()

    def preonce(self, start, end):
        pass

    def oncestart(self, start, end):
        self.once(start, end)

    def once(self, start, end):
        pass

    def prenext(self):
        '''
        在所有 data/indicator 都满足最小 period 前调用。

        Returns:
            None
        '''
        pass

    def nextstart(self):
        '''
        在所有 data/indicator 刚好满足最小 period 时调用一次。

        Returns:
            None

        默认行为是调用 ``next``。
        '''

        # 第一次完整计算时调用一次，默认转到普通 next
        self.next()

    def next(self):
        '''
        所有 data/indicator 满足最小 period 后，对剩余数据点调用。

        Returns:
            None
        '''
        pass

    def _addnotification(self, *args, **kwargs):
        pass

    def _notify(self):
        pass

    def _plotinit(self):
        pass

    def qbuffer(self, savemem=0):
        if savemem:
            for line in self.lines:
                line.qbuffer()

        # 如果调用到这里，下层对象都必须节省内存
        for obj in self._lineiterators[self.IndType]:
            obj.qbuffer(savemem=1)

        # 通知 data 按最小 period 调整 buffer
        for data in self.datas:
            data.minbuffer(self._minperiod)


# 这 3 个子类用于在 LineIterator 内部或外部（例如 LineObservers）识别 3 个分支，
# 同时避免产生循环 import

class DataAccessor(LineIterator):
    '''数据访问基类，用于统一暴露 price line 的枚举别名。'''

    PriceClose = DataSeries.Close
    PriceLow = DataSeries.Low
    PriceHigh = DataSeries.High
    PriceOpen = DataSeries.Open
    PriceVolume = DataSeries.Volume
    PriceOpenInteres = DataSeries.OpenInterest
    PriceDateTime = DataSeries.DateTime


class IndicatorBase(DataAccessor):
    '''indicator 的基类，用于标识 indicator 分支。'''

    pass


class ObserverBase(DataAccessor):
    '''observer 的基类，用于标识 observer 分支。'''

    pass


class StrategyBase(DataAccessor):
    '''strategy 的基类，用于标识 strategy 分支。'''

    pass


# 用于耦合不同长度 line/lineiterator 的工具类
# 只有向 Cerebro 传入 runonce=False 时才可用

class SingleCoupler(LineActions):
    '''单线 coupler，用于在不同长度的 line 之间保持最近一个可用值。'''

    def __init__(self, cdata, clock=None):
        super(SingleCoupler, self).__init__()
        self._clock = clock if clock is not None else self._owner

        self.cdata = cdata
        self.dlen = 0
        self.val = float('NaN')

    def next(self):
        if len(self.cdata) > self.dlen:
            self.val = self.cdata[0]
            self.dlen += 1

        self[0] = self.val


class MultiCoupler(LineIterator):
    '''多线 coupler，用于在不同长度的 multiline 对象之间保持最近一组可用值。'''

    _ltype = LineIterator.IndType

    def __init__(self):
        super(MultiCoupler, self).__init__()
        self.dlen = 0
        self.dsize = self.fullsize()  # line 数量的快捷缓存
        self.dvals = [float('NaN')] * self.dsize

    def next(self):
        if len(self.data) > self.dlen:
            self.dlen += 1

            for i in range(self.dsize):
                self.dvals[i] = self.data.lines[i][0]

        for i in range(self.dsize):
            self.lines[i][0] = self.dvals[i]


def LinesCoupler(cdata, clock=None, **kwargs):
    if isinstance(cdata, LineSingle):
        return SingleCoupler(cdata, clock)  # 单线对象直接返回 SingleCoupler

    cdatacls = cdata.__class__  # 创建前复制重要结构
    try:
        LinesCoupler.counter += 1  # 用于唯一类名的计数器
    except AttributeError:
        LinesCoupler.counter = 0

    # 准备 MultiCoupler 子类
    nclsname = str('LinesCoupler_%d' % LinesCoupler.counter)
    ncls = type(nclsname, (MultiCoupler,), {})
    thismod = sys.modules[LinesCoupler.__module__]
    setattr(thismod, ncls.__name__, ncls)
    # 替换 lines 等结构，得到语义合理的 clone
    ncls.lines = cdatacls.lines
    ncls.params = cdatacls.params
    ncls.plotinfo = cdatacls.plotinfo
    ncls.plotlines = cdatacls.plotlines

    obj = ncls(cdata, **kwargs)  # 实例化
    # 在这里设置 clock，避免它被 LineIterator 的后台扫描逻辑解释为 data
    if clock is None:
        clock = getattr(cdata, '_clock', None)
        if clock is not None:
            nclock = getattr(clock, '_clock', None)
            if nclock is not None:
                clock = nclock
            else:
                nclock = getattr(clock, 'data', None)
                if nclock is not None:
                    clock = nclock

        if clock is None:
            clock = obj._owner

    obj._clock = clock
    return obj


# 添加一个别名；对 “Single Line” 来说这个名字更自然
LineCoupler = LinesCoupler
