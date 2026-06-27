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

.. module:: lineroot

定义 ``LineRoot`` 基类，以及 ``LineSingle`` / ``LineMultiple`` 基类，用于为真正
执行计算的 line 类建立接口和继承层级。

.. moduleauthor:: Daniel Rodriguez

'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import operator

from .utils.py3 import range, with_metaclass

from . import metabase


class MetaLineRoot(metabase.MetaParams):
    '''
    ``LineRoot`` 的 metaclass，用于在对象创建后、``__init__`` 前寻找并记录 owner。
    '''

    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineRoot, cls).donew(*args, **kwargs)

        # 查找并保存 owner
        # startlevel = 4 ... 用于跳过中间调用栈
        ownerskip = kwargs.pop('_ownerskip', None)
        _obj._owner = metabase.findowner(_obj,
                                         _obj._OwnerCls or LineMultiple,
                                         skip=ownerskip)

        # 参数值此时已经在 __init__ 前设置完毕
        return _obj, args, kwargs


class LineRoot(with_metaclass(MetaLineRoot, object)):
    '''
    ``LineXXX`` 单线和多线实例的基类，用于定义共同接口。

    主要覆盖 period 管理、迭代管理、单/双操作数运算管理，以及 rich comparison
    操作符定义。
    '''
    _OwnerCls = None
    _minperiod = 1
    _opstage = 1

    IndType, StratType, ObsType = range(3)

    def _stage1(self):
        self._opstage = 1

    def _stage2(self):
        self._opstage = 2

    def _operation(self, other, operation, r=False, intify=False):
        if self._opstage == 1:
            return self._operation_stage1(
                other, operation, r=r, intify=intify)

        return self._operation_stage2(other, operation, r=r)

    def _operationown(self, operation):
        if self._opstage == 1:
            return self._operationown_stage1(operation)

        return self._operationown_stage2(operation)

    def qbuffer(self, savemem=0):
        '''切换 line，使其使用最小尺寸 qbuffer 方案。

        Args:
            savemem: 是否启用更省内存的 buffer 模式。

        Returns:
            None
        '''
        raise NotImplementedError

    def minbuffer(self, size):
        '''接收最小 buffer 尺寸通知。

        Args:
            size: buffer 至少需要保证的尺寸。

        Returns:
            None
        '''
        raise NotImplementedError

    def setminperiod(self, minperiod):
        '''
        直接设置 minperiod。

        Args:
            minperiod: 要设置的最小 period。

        Returns:
            None

        例如 strategy 可用它避免等待所有 indicator 都产出值。
        '''
        self._minperiod = minperiod

    def updateminperiod(self, minperiod):
        '''
        在需要时更新 minperiod。

        Args:
            minperiod: 外部计算出的 minperiod；大于当前值时接管当前值。

        Returns:
            None
        '''
        self._minperiod = max(self._minperiod, minperiod)

    def addminperiod(self, minperiod):
        '''
        向自身增加 minperiod，由子类定义具体行为。

        Args:
            minperiod: 要增加的 minperiod。

        Returns:
            None
        '''
        raise NotImplementedError

    def incminperiod(self, minperiod):
        '''
        不做额外折算，直接递增 minperiod。

        Args:
            minperiod: 要递增的 minperiod。

        Returns:
            None
        '''
        raise NotImplementedError

    def prenext(self):
        '''
        在迭代的 ``minperiod`` 阶段调用。

        Returns:
            None
        '''
        pass

    def nextstart(self):
        '''
        在 minperiod 阶段结束后的第一个值上调用。

        Returns:
            None

        该方法只调用一次，默认自动调用 ``next``。
        '''
        self.next()

    def next(self):
        '''
        minperiod 结束后用于逐 bar 计算值。

        Returns:
            None
        '''
        pass

    def preonce(self, start, end):
        '''
        在 ``once`` 迭代的 ``minperiod`` 阶段调用。

        Args:
            start: 起始位置。
            end: 结束位置。

        Returns:
            None
        '''
        pass

    def oncestart(self, start, end):
        '''
        在 minperiod 阶段结束后的第一个 ``once`` 值上调用。

        Args:
            start: 起始位置。
            end: 结束位置。

        Returns:
            None

        该方法只调用一次，默认自动调用 ``once``。
        '''
        self.once(start, end)

    def once(self, start, end):
        '''
        minperiod 结束后用于批量计算值。

        Args:
            start: 起始位置。
            end: 结束位置。

        Returns:
            None
        '''
        pass

    # 算术操作符
    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        raise NotImplementedError

    def _makeoperationown(self, operation, _ownerskip=None):
        raise NotImplementedError

    def _operationown_stage1(self, operation):
        '''
        构建以 ``self`` 为唯一操作数的运算。

        Args:
            operation: 要应用的运算函数。

        Returns:
            LineRoot: 表示该运算的 line 对象。
        '''
        return self._makeoperationown(operation, _ownerskip=self)

    def _roperation(self, other, operation, intify=False):
        '''
        通过 ``self._operation`` 构建反向运算。

        Args:
            other: 另一个操作数。
            operation: 要应用的运算函数。
            intify: 是否把结果转换为整数语义。

        Returns:
            LineRoot: 表示该反向运算的 line 对象或运算结果。
        '''
        return self._operation(other, operation, r=True, intify=intify)

    def _operation_stage1(self, other, operation, r=False, intify=False):
        '''
        构建两个操作数的运算。

        Args:
            other: 另一个操作数；如果是 ``LineMultiple``，会使用其第一条 line。
            operation: 要应用的运算函数。
            r: 是否反向运算。
            intify: 是否把结果转换为整数语义。

        Returns:
            LineRoot: 表示该运算的 line 对象。
        '''
        if isinstance(other, LineMultiple):
            other = other.lines[0]

        return self._makeoperation(other, operation, r, self)

    def _operation_stage2(self, other, operation, r=False):
        '''
        在运行阶段执行 rich comparison 或其他即时运算。

        Args:
            other: 另一个操作数；如果是 ``LineRoot``，会取其当前值。
            operation: 要应用的运算函数。
            r: 是否反向运算。

        Returns:
            object: 运算结果。
        '''
        if isinstance(other, LineRoot):
            other = other[0]

        # operation(float, other) ... 这里预期 other 是 float
        if r:
            return operation(other, self[0])

        return operation(self[0], other)

    def _operationown_stage2(self, operation):
        return operation(self[0])

    def __add__(self, other):
        return self._operation(other, operator.__add__)

    def __radd__(self, other):
        return self._roperation(other, operator.__add__)

    def __sub__(self, other):
        return self._operation(other, operator.__sub__)

    def __rsub__(self, other):
        return self._roperation(other, operator.__sub__)

    def __mul__(self, other):
        return self._operation(other, operator.__mul__)

    def __rmul__(self, other):
        return self._roperation(other, operator.__mul__)

    def __div__(self, other):
        return self._operation(other, operator.__div__)

    def __rdiv__(self, other):
        return self._roperation(other, operator.__div__)

    def __floordiv__(self, other):
        return self._operation(other, operator.__floordiv__)

    def __rfloordiv__(self, other):
        return self._roperation(other, operator.__floordiv__)

    def __truediv__(self, other):
        return self._operation(other, operator.__truediv__)

    def __rtruediv__(self, other):
        return self._roperation(other, operator.__truediv__)

    def __pow__(self, other):
        return self._operation(other, operator.__pow__)

    def __rpow__(self, other):
        return self._roperation(other, operator.__pow__)

    def __abs__(self):
        return self._operationown(operator.__abs__)

    def __neg__(self):
        return self._operationown(operator.__neg__)

    def __lt__(self, other):
        return self._operation(other, operator.__lt__)

    def __gt__(self, other):
        return self._operation(other, operator.__gt__)

    def __le__(self, other):
        return self._operation(other, operator.__le__)

    def __ge__(self, other):
        return self._operation(other, operator.__ge__)

    def __eq__(self, other):
        return self._operation(other, operator.__eq__)

    def __ne__(self, other):
        return self._operation(other, operator.__ne__)

    def __nonzero__(self):
        return self._operationown(bool)

    __bool__ = __nonzero__

    # Python 3 中，如果类重定义了 __eq__，就必须显式实现 hash
    __hash__ = object.__hash__


class LineMultiple(LineRoot):
    '''
    多线 ``LineXXX`` 实例的基类，用于管理包含多条 line 的对象。
    '''
    def reset(self):
        self._stage1()
        self.lines.reset()

    def _stage1(self):
        super(LineMultiple, self)._stage1()
        for line in self.lines:
            line._stage1()

    def _stage2(self):
        super(LineMultiple, self)._stage2()
        for line in self.lines:
            line._stage2()

    def addminperiod(self, minperiod):
        '''
        把传入的 minperiod 下发给所有 line。

        Args:
            minperiod: 要下发的 minperiod。

        Returns:
            None
        '''
        # 下发给所有 line
        for line in self.lines:
            line.addminperiod(minperiod)

    def incminperiod(self, minperiod):
        '''
        把传入的 minperiod 递增量下发给所有 line。

        Args:
            minperiod: 要下发的 minperiod 增量。

        Returns:
            None
        '''
        # 下发给所有 line
        for line in self.lines:
            line.incminperiod(minperiod)

    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        return self.lines[0]._makeoperation(other, operation, r, _ownerskip)

    def _makeoperationown(self, operation, _ownerskip=None):
        return self.lines[0]._makeoperationown(operation, _ownerskip)

    def qbuffer(self, savemem=0):
        for line in self.lines:
            line.qbuffer(savemem=1)

    def minbuffer(self, size):
        for line in self.lines:
            line.minbuffer(size)


class LineSingle(LineRoot):
    '''
    单线 ``LineXXX`` 实例的基类，用于管理只包含一条 line 的对象。
    '''
    def addminperiod(self, minperiod):
        '''
        增加 minperiod，并扣除重叠的 1 个最小 period。

        Args:
            minperiod: 要增加的 minperiod。

        Returns:
            None
        '''
        self._minperiod += minperiod - 1

    def incminperiod(self, minperiod):
        '''
        不做额外折算，直接递增 minperiod。

        Args:
            minperiod: 要递增的 minperiod。

        Returns:
            None
        '''
        self._minperiod += minperiod
