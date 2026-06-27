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
'''

.. module:: linebuffer

保存 *line* buffer 的类，并提供 append、forward、rewind、reset 等操作。

.. moduleauthor:: Daniel Rodriguez

'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import array
import collections
import datetime
from itertools import islice
import math

from .utils.py3 import range, with_metaclass, string_types

from .lineroot import LineRoot, LineSingle, LineMultiple
from . import metabase
from .utils import num2date, time2num


NAN = float('NaN')


class LineBuffer(LineSingle):
    '''
    单条 line 的 buffer 类，用于保存当前值、历史值和必要的未来扩展值。

    索引 ``0`` 始终指向当前输入/输出位置；正索引读取过去的值，负索引读取未来扩展值
    （如果右侧已经扩展）。

    Args:
        无

    Returns:
        LineBuffer: 可被 line 系统使用的单线 buffer。

    ---
    交互界面使用示范:

    >>> line = LineBuffer()
    >>> line.forward(value=10.0)
    >>> line[0]
    10.0

    该类也可以绑定其他 ``LineBuffer``。当前 line 设置值时，会同步写入绑定 line。
    '''

    UnBounded, QBuffer = (0, 1)

    def __init__(self):
        self.lines = [self]
        self.mode = self.UnBounded
        self.bindings = list()
        self.reset()
        self._tz = None

    def get_idx(self):
        return self._idx

    def set_idx(self, idx, force=False):
        # QBuffer 已到达 buffer 最后位置时，除非 force，否则保持它作为索引 0。
        # 这支持 resampling：forward 增加一个位置并丢弃第一个位置，但 0 保持不变。
        # force 用于 replaying；replaying 需要额外 bar 可以前后浮动，因为读到最后输入后，
        # 会用 backwards 更新上一条数据。如果位置 0 没有移到前一个索引，就会失败。
        if self.mode == self.QBuffer:
            if force or self._idx < self.lenmark:
                self._idx = idx
        else:  # default: UnBounded
            self._idx = idx

    idx = property(get_idx, set_idx)

    def reset(self):
        '''重置内部 buffer 结构和索引。

        Returns:
            None
        '''
        if self.mode == self.QBuffer:
            # 添加 extrasize 以保证 resample/replay 可用。它们会用 backwards 擦除
            # 最后一个 bar/tick，再交付新的 bar。此前的 forward 可能已经丢弃了 period
            # 之前的 bar，无法找回；额外 +1 可以在 forward 时保留该 bar。
            self.array = collections.deque(maxlen=self.maxlen + self.extrasize)
            self.useislice = True
        else:
            self.array = array.array(str('d'))
            self.useislice = False

        self.lencount = 0
        self.idx = -1
        self.extension = 0

    def qbuffer(self, savemem=0, extrasize=0):
        self.mode = self.QBuffer
        self.maxlen = self._minperiod
        self.extrasize = extrasize
        self.lenmark = self.maxlen - (not self.extrasize)
        self.reset()

    def getindicators(self):
        return []

    def minbuffer(self, size):
        '''保证 linebuffer 至少拥有请求的尺寸。

        Args:
            size: 需要保证的最小 buffer 尺寸。

        Returns:
            None

        非 QBuffer 模式下该条件总是满足；QBuffer 模式下，如果当前尺寸不足，需要调整
        buffer。
        '''
        if self.mode != self.QBuffer or self.maxlen >= size:
            return

        self.maxlen = size
        self.lenmark = self.maxlen - (not self.extrasize)
        self.reset()

    def __len__(self):
        return self.lencount

    def buflen(self):
        '''返回内部 buffer 当前可保存的真实数据量。

        Returns:
            int: 当前真实数据容量，不包含为 lookahead 保留的扩展区。
        '''
        return len(self.array) - self.extension

    def __getitem__(self, ago):
        return self.array[self.idx + ago]

    def get(self, ago=0, size=1):
        '''返回相对 ``ago`` 的数组切片。

        Args:
            ago: 切片参考位置。
            size: 返回切片的长度，可为正数或负数。

        Returns:
            list | array.array: 底层 buffer 的切片。

        ``size`` 为正数时，``ago`` 表示 iterable 的结束位置；为负数时含义相反。
        '''
        if self.useislice:
            start = self.idx + ago - size + 1
            end = self.idx + ago + 1
            return list(islice(self.array, start, end))

        return self.array[self.idx + ago - size + 1:self.idx + ago + 1]

    def getzeroval(self, idx=0):
        '''返回相对 buffer 真实零点的单个值。

        Args:
            idx: 相对真实起点的位置。

        Returns:
            float: 底层 buffer 中的单个值。
        '''
        return self.array[idx]

    def getzero(self, idx=0, size=1):
        '''返回相对 buffer 真实零点的切片。

        Args:
            idx: 相对真实起点的位置。
            size: 返回切片的长度。

        Returns:
            list | array.array: 底层 buffer 的切片。
        '''
        if self.useislice:
            return list(islice(self.array, idx, idx + size))

        return self.array[idx:idx + size]

    def __setitem__(self, ago, value):
        '''在 ``ago`` 位置设置值，并执行关联 binding。

        Args:
            ago: 要写入的相对位置。
            value: 要设置的值。

        Returns:
            None
        '''
        self.array[self.idx + ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        '''在 ``ago`` 位置设置值，并执行关联 binding。

        Args:
            value: 要设置的值。
            ago: 要写入的相对位置。

        Returns:
            None
        '''
        self.array[self.idx + ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def home(self):
        '''把逻辑索引倒回开始位置。

        Returns:
            None

        底层 buffer 不会被修改，实际长度可通过 ``buflen`` 查询。
        '''
        self.idx = -1
        self.lencount = 0

    def forward(self, value=NAN, size=1):
        '''向前移动逻辑索引，并按需扩展 buffer。

        Args:
            value: 新位置填入的值。
            size: 要新增的位置数量。

        Returns:
            None
        '''
        self.idx += size
        self.lencount += size

        for i in range(size):
            self.array.append(value)

    def backwards(self, size=1, force=False):
        '''向后移动逻辑索引，并按需缩小 buffer。

        Args:
            size: 要回退并缩减的位置数量。
            force: 是否强制移动 QBuffer 的索引。

        Returns:
            None
        '''
        # 直接调用属性 setter，以支持 force
        self.set_idx(self._idx - size, force=force)
        self.lencount -= size
        for i in range(size):
            self.array.pop()

    def rewind(self, size=1):
        self.idx -= size
        self.lencount -= size

    def advance(self, size=1):
        '''只前进逻辑索引，不修改底层 buffer。

        Args:
            size: 要前进的位置数量。

        Returns:
            None
        '''
        self.idx += size
        self.lencount += size

    def extend(self, value=NAN, size=0):
        '''扩展底层数组，新增当前索引不会到达的位置。

        Args:
            value: 新位置填入的值。
            size: 要新增的位置数量。

        Returns:
            None

        主要用于 lookahead，或向 buffer 的“未来”位置设置值。
        '''
        self.extension += size
        for i in range(size):
            self.array.append(value)

    def addbinding(self, binding):
        '''添加另一个 line binding。

        Args:
            binding: 当前 line 设置值时也要同步设置的另一个 ``LineBuffer``。

        Returns:
            None
        '''
        self.bindings.append(binding)
        # 在 binding 中记录 period 开始位置（永远不早于当前对象）
        binding.updateminperiod(self._minperiod)

    def plot(self, idx=0, size=None):
        '''返回相对 buffer 真实零点的绘图切片。

        Args:
            idx: 相对真实起点的位置。
            size: 返回切片的长度；为空时返回整个 buffer。

        Returns:
            list | array.array: 底层 buffer 的切片。

        这是 ``getzero`` 的变体，默认返回整个 buffer，符合绘图时“全部都要画”的语义。
        '''
        return self.getzero(idx, size or len(self))

    def plotrange(self, start, end):
        if self.useislice:
            return list(islice(self.array, start, end))

        return self.array[start:end]

    def oncebinding(self):
        '''
        在 ``once`` 模式下执行 binding。

        Returns:
            None
        '''
        larray = self.array
        blen = self.buflen()
        for binding in self.bindings:
            binding.array[0:blen] = larray[0:blen]

    def bind2lines(self, binding=0):
        '''
        保存到另一条 line 的 binding。

        Args:
            binding: line 索引或 line 名称。

        Returns:
            LineBuffer: 当前对象自身。
        '''
        if isinstance(binding, string_types):
            line = getattr(self._owner.lines, binding)
        else:
            line = self._owner.lines[binding]

        self.addbinding(line)

        return self

    bind2line = bind2lines

    def __call__(self, ago=None):
        '''返回延迟版本或 timeframe 适配版本。

        Args:
            ago: ``None`` 或 ``LineRoot`` 时返回 ``LineCoupler``；其他情况按整数处理，
                返回 ``LineDelay``。

        Returns:
            LineCoupler | LineDelay: 适配或延迟后的 line 对象。
        '''
        from .lineiterator import LineCoupler
        if ago is None or isinstance(ago, LineRoot):
            return LineCoupler(self, ago)

        return LineDelay(self, ago)

    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        return LinesOperation(self, other, operation, r=r,
                              _ownerskip=_ownerskip)

    def _makeoperationown(self, operation, _ownerskip=None):
        return LineOwnOperation(self, operation, _ownerskip=_ownerskip)

    def _settz(self, tz):
        self._tz = tz

    def datetime(self, ago=0, tz=None, naive=True):
        return num2date(self.array[self.idx + ago],
                        tz=tz or self._tz, naive=naive)

    def date(self, ago=0, tz=None, naive=True):
        return num2date(self.array[self.idx + ago],
                        tz=tz or self._tz, naive=naive).date()

    def time(self, ago=0, tz=None, naive=True):
        return num2date(self.array[self.idx + ago],
                        tz=tz or self._tz, naive=naive).time()

    def dt(self, ago=0):
        '''
        返回 datetime float 的数字日期部分。

        Args:
            ago: 相对当前位置。

        Returns:
            int: 日期部分。
        '''
        return math.trunc(self.array[self.idx + ago])

    def tm_raw(self, ago=0):
        '''
        返回 datetime float 的原始数字时间部分。

        Args:
            ago: 相对当前位置。

        Returns:
            float: 未转换的时间小数部分。
        '''
        # 命名为 raw，是因为它直接取小数部分，不转换为 time，以避免受日期计数
        # （编码整数部分）影响
        return math.modf(self.array[self.idx + ago])[0]

    def tm(self, ago=0):
        '''
        返回 datetime float 的数字时间部分。

        Args:
            ago: 相对当前位置。

        Returns:
            float: 转换后的时间部分。
        '''
        # 为避免精度误差，先转换为 datetime.time 对象，再返回小数时间部分，
        # 用于后续比较
        return time2num(num2date(self.array[self.idx + ago]).time())

    def tm_lt(self, other, ago=0):
        '''
        比较当前 datetime float 的时间部分是否小于 ``other``。

        Args:
            other: 要比较的数字时间部分。
            ago: 相对当前位置。

        Returns:
            bool: 比较结果。
        '''
        # 比较原始 tm（编码 datetime 的小数部分）和当前 datetime 的 tm 时，
        # 需要把原始 tm 同步到当前 day count（整数部分）上
        dtime = self.array[self.idx + ago]
        tm, dt = math.modf(dtime)

        return dtime < (dt + other)

    def tm_le(self, other, ago=0):
        '''
        比较当前 datetime float 的时间部分是否小于等于 ``other``。

        Args:
            other: 要比较的数字时间部分。
            ago: 相对当前位置。

        Returns:
            bool: 比较结果。
        '''
        # 比较原始 tm 和当前 datetime 的 tm 时，需要同步到当前 day count 上
        dtime = self.array[self.idx + ago]
        tm, dt = math.modf(dtime)

        return dtime <= (dt + other)

    def tm_eq(self, other, ago=0):
        '''
        比较当前 datetime float 的时间部分是否等于 ``other``。

        Args:
            other: 要比较的数字时间部分。
            ago: 相对当前位置。

        Returns:
            bool: 比较结果。
        '''
        # 比较原始 tm 和当前 datetime 的 tm 时，需要同步到当前 day count 上
        dtime = self.array[self.idx + ago]
        tm, dt = math.modf(dtime)

        return dtime == (dt + other)

    def tm_gt(self, other, ago=0):
        '''
        比较当前 datetime float 的时间部分是否大于 ``other``。

        Args:
            other: 要比较的数字时间部分。
            ago: 相对当前位置。

        Returns:
            bool: 比较结果。
        '''
        # 比较原始 tm 和当前 datetime 的 tm 时，需要同步到当前 day count 上
        dtime = self.array[self.idx + ago]
        tm, dt = math.modf(dtime)

        return dtime > (dt + other)

    def tm_ge(self, other, ago=0):
        '''
        比较当前 datetime float 的时间部分是否大于等于 ``other``。

        Args:
            other: 要比较的数字时间部分。
            ago: 相对当前位置。

        Returns:
            bool: 比较结果。
        '''
        # 比较原始 tm 和当前 datetime 的 tm 时，需要同步到当前 day count 上
        dtime = self.array[self.idx + ago]
        tm, dt = math.modf(dtime)

        return dtime >= (dt + other)

    def tm2dtime(self, tm, ago=0):
        '''
        把给定 ``tm`` 转换到 ``ago`` bar 所在 datetime 的日期框架中。

        Args:
            tm: 数字时间部分。
            ago: 相对当前位置。

        Returns:
            float: 可比较的 datetime float。

        该方法适合外部比较，可避免精度误差。
        '''
        return int(self.array[self.idx + ago]) + tm

    def tm2datetime(self, tm, ago=0):
        '''
        把给定 ``tm`` 转换到 ``ago`` bar 所在日期上的 ``datetime``。

        Args:
            tm: 数字时间部分。
            ago: 相对当前位置。

        Returns:
            datetime.datetime: 转换后的 datetime。

        该方法适合外部比较，可避免精度误差。
        '''
        return num2date(int(self.array[self.idx + ago]) + tm)


class MetaLineActions(LineBuffer.__class__):
    '''
    ``LineActions`` 的 metaclass，用于在 init 前扫描 line 并计算 minperiod。

    postinit 阶段会把实例注册到 owner；owner 已经由 ``LineRoot`` 基类的 metaclass
    找到。
    '''
    _acache = dict()
    _acacheuse = False

    @classmethod
    def cleancache(cls):
        cls._acache = dict()

    @classmethod
    def usecache(cls, onoff):
        cls._acacheuse = onoff

    def __call__(cls, *args, **kwargs):
        if not cls._acacheuse:
            return super(MetaLineActions, cls).__call__(*args, **kwargs)

        # 实现缓存，避免重复创建 line action
        ckey = (cls, tuple(args), tuple(kwargs.items()))  # tuple 可 hash
        try:
            return cls._acache[ckey]
        except TypeError:  # 存在不可 hash 的对象
            return super(MetaLineActions, cls).__call__(*args, **kwargs)
        except KeyError:
            pass  # 可 hash，但不在缓存中

        _obj = super(MetaLineActions, cls).__call__(*args, **kwargs)
        return cls._acache.setdefault(ckey, _obj)

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineActions, cls).dopreinit(_obj, *args, **kwargs)

        _obj._clock = _obj._owner  # 默认设置

        if isinstance(args[0], LineRoot):
            _obj._clock = args[0]

        # 保存 data 引用，供后续调整 buffer 使用
        _obj._datas = [x for x in args if isinstance(x, LineRoot)]

        # operation line 自身产出前，不产出任何值
        _minperiods = [x._minperiod for x in args if isinstance(x, LineSingle)]

        mlines = [x.lines[0] for x in args if isinstance(x, LineMultiple)]
        _minperiods += [x._minperiod for x in mlines]

        _minperiod = max(_minperiods or [1])

        # 按需更新自身 minperiod
        _obj.updateminperiod(_minperiod)

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineActions, cls).dopostinit(_obj, *args, **kwargs)

        # 注册到 _owner，后续由 owner 驱动
        _obj._owner.addindicator(_obj)

        return _obj, args, kwargs


class PseudoArray(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getitem__(self, key):
        return self.wrapped

    @property
    def array(self):
        return self


class LineActions(with_metaclass(MetaLineActions, LineBuffer)):
    '''
    派生自 ``LineBuffer`` 的 line action 基类，用于提供与 ``LineIterator`` 兼容的
    最小接口。

    该类提供可执行的 ``_next`` 和 ``_once`` 接口；metaclass 负责计算 minperiod 和注册
    到 owner。
    '''

    _ltype = LineBuffer.IndType

    def getindicators(self):
        return []

    def qbuffer(self, savemem=0):
        super(LineActions, self).qbuffer(savemem=savemem)
        for data in self._datas:
            data.minbuffer(size=self._minperiod)

    @staticmethod
    def arrayize(obj):
        if isinstance(obj, LineRoot):
            if not isinstance(obj, LineSingle):
                obj = obj.lines[0]  # 从 multiline 中取第 1 条 line
        else:
            obj = PseudoArray(obj)

        return obj

    def _next(self):
        clock_len = len(self._clock)
        if clock_len > len(self):
            self.forward()

        if clock_len > self._minperiod:
            self.next()
        elif clock_len == self._minperiod:
            # 只在第 1 个完整值时调用
            self.nextstart()
        else:
            self.prenext()

    def _once(self):
        self.forward(size=self._clock.buflen())
        self.home()

        self.preonce(0, self._minperiod - 1)
        self.oncestart(self._minperiod - 1, self._minperiod)
        self.once(self._minperiod, self.buflen())

        self.oncebinding()


def LineDelay(a, ago=0, **kwargs):
    if ago <= 0:
        return _LineDelay(a, ago, **kwargs)

    return _LineForward(a, ago, **kwargs)


def LineNum(num):
    return LineDelay(PseudoArray(num))


class _LineDelay(LineActions):
    '''
    line 延迟类，用于从 ``ago`` 个周期前取值，从而延迟数据交付。
    '''
    def __init__(self, a, ago):
        super(_LineDelay, self).__init__()
        self.a = a
        self.ago = ago

        # 需要把 delay 加到 period 中。ago 从 0 开始，因此要额外传 1；这是任何 data
        # 定义的最小 period，并会在 addminperiod 中被扣除
        self.addminperiod(abs(ago) + 1)

    def next(self):
        self[0] = self.a[self.ago]

    def once(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        src = self.a.array
        ago = self.ago

        for i in range(start, end):
            dst[i] = src[i + ago]


class _LineForward(LineActions):
    '''
    line 前向类，用于把未来 ``ago`` 个周期的值写入当前延迟结构。
    '''
    def __init__(self, a, ago):
        super(_LineForward, self).__init__()
        self.a = a
        self.ago = ago

        # 需要把 delay 加到 period 中。ago 从 0 开始，因此要额外传 1；这是任何 data
        # 定义的最小 period，并会在 addminperiod 中被扣除
        # self.addminperiod(abs(ago) + 1)
        if ago > self.a._minperiod:
            self.addminperiod(ago - self.a._minperiod + 1)

    def next(self):
        self[-self.ago] = self.a[0]

    def once(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        src = self.a.array
        ago = self.ago

        for i in range(start, end):
            dst[i - ago] = src[i]


class LinesOperation(LineActions):

    '''
    双操作数 line 运算类，用于保存并执行类似 ``mul`` 的运算。

    每次 ``next`` 或遍历数组时，会把运算应用到两个操作数，并把结果存入自身。

    为了优化执行并减少条件判断，会根据运算方向（普通或反向）和操作数性质
    （``LineBuffer`` 或非 ``LineBuffer``）选择对应的 ``next`` / ``once`` 实现。

    ``once`` 运算中本可以使用 ``map``，例如::

        operated = map(self.operation, srca[start:end], srcb[start:end])
        self.array[start:end] = array.array(str(self.typecode), operated)

    实测没有明显执行收益，因此保留显式循环以增强可读性。
    '''

    def __init__(self, a, b, operation, r=False):
        super(LinesOperation, self).__init__()

        self.operation = operation
        self.a = a  # 始终是 linebuffer
        self.b = b

        self.r = r
        self.bline = isinstance(b, LineBuffer)
        self.btime = isinstance(b, datetime.time)
        self.bfloat = not self.bline and not self.btime

        if r:
            self.a, self.b = b, a

    def next(self):
        if self.bline:
            self[0] = self.operation(self.a[0], self.b[0])
        elif not self.r:
            if not self.btime:
                self[0] = self.operation(self.a[0], self.b)
            else:
                self[0] = self.operation(self.a.time(), self.b)
        else:
            self[0] = self.operation(self.a, self.b[0])

    def once(self, start, end):
        if self.bline:
            self._once_op(start, end)
        elif not self.r:
            if not self.btime:
                self._once_val_op(start, end)
            else:
                self._once_time_op(start, end)
        else:
            self._once_val_op_r(start, end)

    def _once_op(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        op = self.operation

        for i in range(start, end):
            dst[i] = op(srca[i], srcb[i])

    def _once_time_op(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        srca = self.a.array
        srcb = self.b
        op = self.operation
        tz = self._tz

        for i in range(start, end):
            dst[i] = op(num2date(srca[i], tz=tz).time(), srcb)

    def _once_val_op(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        srca = self.a.array
        srcb = self.b
        op = self.operation

        for i in range(start, end):
            dst[i] = op(srca[i], srcb)

    def _once_val_op_r(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        srca = self.a
        srcb = self.b.array
        op = self.operation

        for i in range(start, end):
            dst[i] = op(srca, srcb[i])


class LineOwnOperation(LineActions):
    '''
    单操作数 line 运算类，用于保存并执行类似 ``abs`` 的运算。

    每次 ``next`` 或遍历数组时，会应用运算并把结果存入自身。
    '''
    def __init__(self, a, operation):
        super(LineOwnOperation, self).__init__()

        self.operation = operation
        self.a = a

    def next(self):
        self[0] = self.operation(self.a[0])

    def once(self, start, end):
        # 缓存 Python 字典查找
        dst = self.array
        srca = self.a.array
        op = self.operation

        for i in range(start, end):
            dst[i] = op(srca[i])
