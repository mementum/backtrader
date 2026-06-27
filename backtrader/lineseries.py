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

定义 ``LineSeries`` 及其 descriptor，用于一次持有多条 line 的类。

.. moduleauthor:: Daniel Rodriguez

'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from .utils.py3 import map, range, string_types, with_metaclass

from .linebuffer import LineBuffer, LineActions, LinesOperation, LineDelay, NAN
from .lineroot import LineRoot, LineSingle, LineMultiple
from .metabase import AutoInfoClass
from . import metabase


class LineAlias(object):
    '''line alias descriptor，用于保存 line 引用并从 owner 返回对应 line。

    Args:
        line: owner 的 ``lines`` buffer 中要返回的 line 索引。

    Returns:
        LineAlias: 可绑定到类属性上的 line descriptor。

    为了使用便利，descriptor 的 ``__set__`` 不会修改 line 引用，因为该引用在
    descriptor 生命周期内是常量；它实际设置的是当前时刻（索引 ``0``）的 line 值。
    '''

    def __init__(self, line):
        self.line = line

    def __get__(self, obj, cls=None):
        return obj.lines[self.line]

    def __set__(self, obj, value):
        '''
        设置当前 line 的值。

        Args:
            obj: descriptor 所属对象。
            value: 要绑定或写入的 line 值。

        Returns:
            None

        line 创建后不能替换自身，但可以设置其中的值；这里通过给 ``value`` 内部 line
        添加 binding 来实现。
        '''
        if isinstance(value, LineMultiple):
            value = value.lines[0]

        # 如果确定为 LineBuffer 的 value 不是 LineActions，下面的 binding 可能过早触发，
        # 把值写入尚未 forward 的 line，等价于提前 1 个索引写入，破坏 next 模式逻辑。
        # 因此需要把它转换为 0 延迟的 LineDelay 对象。
        if not isinstance(value, LineActions):
            value = value(0)

        value.addbinding(obj.lines[self.line])


class Lines(object):
    '''
    多条 line 的容器类，用于提供类似 ``LineBuffer`` 的批量接口。

    Args:
        无

    Returns:
        Lines: 可持有多条 line 的容器。

    ``forward``、``rewind``、``advance`` 等操作会转发到自身持有的所有 line。
    该类还可以通过 ``_derive`` 自动派生子类，以按定义顺序保存新 line。
    '''
    _getlinesbase = classmethod(lambda cls: ())
    _getlines = classmethod(lambda cls: ())
    _getlinesextra = classmethod(lambda cls: 0)
    _getlinesextrabase = classmethod(lambda cls: 0)

    @classmethod
    def _derive(cls, name, lines, extralines, otherbases, linesoverride=False,
                lalias=None):
        '''
        创建 ``Lines`` 子类。

        Args:
            name: 新类名后缀。
            lines: 新增 line 定义。
            extralines: 需要额外创建的 line 数量。
            otherbases: 其他基类中已有的 line 定义。
            linesoverride: 是否丢弃所有基类 line，并以顶层 ``Lines`` 作为基类创建新层级。
            lalias: 额外 line alias 定义。

        Returns:
            type: 派生出的 ``Lines`` 子类。
        '''
        obaseslines = ()
        obasesextralines = 0

        for otherbase in otherbases:
            if isinstance(otherbase, tuple):
                obaseslines += otherbase
            else:
                obaseslines += otherbase._getlines()
                obasesextralines += otherbase._getlinesextra()

        if not linesoverride:
            baselines = cls._getlines() + obaseslines
            baseextralines = cls._getlinesextra() + obasesextralines
        else:  # 覆盖 lines，跳过所有基类内容
            baselines = ()
            baseextralines = 0

        clslines = baselines + lines
        clsextralines = baseextralines + extralines
        lines2add = obaseslines + lines

        # str 用于 Python 2/3 兼容
        basecls = cls if not linesoverride else Lines

        newcls = type(str(cls.__name__ + '_' + name), (basecls,), {})
        clsmodule = sys.modules[cls.__module__]
        newcls.__module__ = cls.__module__
        setattr(clsmodule, str(cls.__name__ + '_' + name), newcls)

        setattr(newcls, '_getlinesbase', classmethod(lambda cls: baselines))
        setattr(newcls, '_getlines', classmethod(lambda cls: clslines))

        setattr(newcls, '_getlinesextrabase',
                classmethod(lambda cls: baseextralines))
        setattr(newcls, '_getlinesextra',
                classmethod(lambda cls: clsextralines))

        l2start = len(cls._getlines()) if not linesoverride else 0
        l2add = enumerate(lines2add, start=l2start)
        l2alias = {} if lalias is None else lalias._getkwargsdefault()
        for line, linealias in l2add:
            if not isinstance(linealias, string_types):
                # 传入了 tuple 或 list，第 1 个元素是名称
                linealias = linealias[0]

            desc = LineAlias(line)  # 保留下面使用的引用
            setattr(newcls, linealias, desc)

        # 为给定名称创建额外 alias。l2alias 来自参数 lalias，也就是 linealias 指令；
        # 这里容易混淆，因为 LineAlias descriptor 来自 lines 指令。
        for line, linealias in enumerate(newcls._getlines()):
            if not isinstance(linealias, string_types):
                # 传入了 tuple 或 list，第 1 个元素是名称
                linealias = linealias[0]

            desc = LineAlias(line)  # 保留下面使用的引用
            if linealias in l2alias:
                extranames = l2alias[linealias]
                if isinstance(linealias, string_types):
                    extranames = [extranames]

                for ename in extranames:
                    setattr(newcls, ename, desc)

        return newcls

    @classmethod
    def _getlinealias(cls, i):
        '''
        按索引返回 line alias。

        Args:
            i: line 索引。

        Returns:
            str: line alias，不存在时返回空字符串。
        '''
        lines = cls._getlines()
        if i >= len(lines):
            return ''
        linealias = lines[i]
        return linealias

    @classmethod
    def getlinealiases(cls):
        return cls._getlines()

    def itersize(self):
        return iter(self.lines[0:self.size()])

    def __init__(self, initlines=None):
        '''
        创建 ``_derive`` 记录的 line，或使用传入的 ``initlines``。

        Args:
            initlines: 可选的初始 line 列表。

        Returns:
            None
        '''
        self.lines = list()
        for line, linealias in enumerate(self._getlines()):
            kwargs = dict()
            self.lines.append(LineBuffer(**kwargs))

        # 添加所需的 extralines
        for i in range(self._getlinesextra()):
            if not initlines:
                self.lines.append(LineBuffer())
            else:
                self.lines.append(initlines[i])

    def __len__(self):
        '''
        代理到第 1 条 line 的长度操作。
        '''
        return len(self.lines[0])

    def size(self):
        return len(self.lines) - self._getlinesextra()

    def fullsize(self):
        return len(self.lines)

    def extrasize(self):
        return self._getlinesextra()

    def __getitem__(self, line):
        '''
        按索引获取 line。
        '''
        return self.lines[line]

    def get(self, ago=0, size=1, line=0):
        '''
        代理到指定 line 的 ``get`` 操作。
        '''
        return self.lines[line].get(ago, size=size)

    def __setitem__(self, line, value):
        '''
        代理到指定 line 的设置操作。
        '''
        setattr(self, self._getlinealias(line), value)

    def forward(self, value=NAN, size=1):
        '''
        对所有 line 执行 ``forward``。
        '''
        for line in self.lines:
            line.forward(value, size=size)

    def backwards(self, size=1, force=False):
        '''
        对所有 line 执行 ``backwards``。
        '''
        for line in self.lines:
            line.backwards(size, force=force)

    def rewind(self, size=1):
        '''
        对所有 line 执行 ``rewind``。
        '''
        for line in self.lines:
            line.rewind(size)

    def extend(self, value=NAN, size=0):
        '''
        对所有 line 执行 ``extend``。
        '''
        for line in self.lines:
            line.extend(value, size)

    def reset(self):
        '''
        对所有 line 执行 ``reset``。
        '''
        for line in self.lines:
            line.reset()

    def home(self):
        '''
        对所有 line 执行 ``home``。
        '''
        for line in self.lines:
            line.home()

    def advance(self, size=1):
        '''
        对所有 line 执行 ``advance``。
        '''
        for line in self.lines:
            line.advance(size)

    def buflen(self, line=0):
        '''
        返回指定 line 的 buffer 长度。
        '''
        return self.lines[line].buflen()


class MetaLineSeries(LineMultiple.__class__):
    '''
    ``LineSeries`` 的 metaclass，用于管理 line、plotinfo 和 plotlines 的类创建与实例创建。

    在 ``__new__`` 阶段读取 ``lines``、``plotinfo``、``plotlines`` 类变量定义，并将
    它们转换为 ``Lines`` 或 ``AutoClassInfo`` 类型的类。

    在实例创建阶段，将这些类替换为对应实例，并为 ``lines`` 实例中持有的 line 添加
    alias。

    剩余 ``kwargs`` 会与 ``plotinfo`` 参数匹配；匹配到的会设置到 ``plotinfo`` 并从
    ``kwargs`` 中移除。该 metaclass 的根类是 ``MetaParams``，因此类中定义的
    ``params`` 已在更早阶段从 ``kwargs`` 中移除。
    '''

    def __new__(meta, name, bases, dct):
        '''
        拦截类创建，识别 ``lines`` / ``plotinfo`` / ``plotlines`` 类属性，并创建对应类
        接管这些属性。
        '''

        # 获取 alias，不把它留给子类继续处理
        aliases = dct.setdefault('alias', ())
        aliased = dct.setdefault('aliased', '')

        # 从类创建字典中取出 line 定义（如果存在）
        linesoverride = dct.pop('linesoverride', False)
        newlines = dct.pop('lines', ())
        extralines = dct.pop('extralines', 0)

        # 取出新的 linealias 定义（如果存在）
        newlalias = dict(dct.pop('linealias', {}))

        # 取出新的 plotinfo/plotlines 定义（如果存在）
        newplotinfo = dict(dct.pop('plotinfo', {}))
        newplotlines = dict(dct.pop('plotlines', {}))

        # 创建类，同时带入已有 lines
        cls = super(MetaLineSeries, meta).__new__(meta, name, bases, dct)

        # 创建 lines 前先检查 line alias
        lalias = getattr(cls, 'linealias', AutoInfoClass)
        oblalias = [x.linealias for x in bases[1:] if hasattr(x, 'linealias')]
        cls.linealias = la = lalias._derive('la_' + name, newlalias, oblalias)

        # 获取实际 lines，或使用默认值
        lines = getattr(cls, 'lines', Lines)

        # 创建带当前类名和新增 line 的 lines 子类，并放回类中
        morebaseslines = [x.lines for x in bases[1:] if hasattr(x, 'lines')]
        cls.lines = lines._derive(name, newlines, extralines, morebaseslines,
                                  linesoverride, lalias=la)

        # 从基类获取 plotinfo/plotlines 副本；不存在时使用默认值
        plotinfo = getattr(cls, 'plotinfo', AutoInfoClass)
        plotlines = getattr(cls, 'plotlines', AutoInfoClass)

        # 创建 plotinfo/plotlines 子类并放回类中
        morebasesplotinfo = \
            [x.plotinfo for x in bases[1:] if hasattr(x, 'plotinfo')]
        cls.plotinfo = plotinfo._derive('pi_' + name, newplotinfo,
                                        morebasesplotinfo)

        # 处理 plotline 前，新增 line 已加入；若没有对应 plotlineinfo，则补默认项
        for line in newlines:
            newplotlines.setdefault(line, dict())

        morebasesplotlines = \
            [x.plotlines for x in bases[1:] if hasattr(x, 'plotlines')]
        cls.plotlines = plotlines._derive(
            'pl_' + name, newplotlines, morebasesplotlines, recurse=True)

        # 创建声明过的类 alias（无修改子类）
        for alias in aliases:
            newdct = {'__doc__': cls.__doc__,
                      '__module__': cls.__module__,
                      'aliased': cls.__name__}

            if not isinstance(alias, string_types):
                # 传入了 tuple 或 list，第 1 个元素是名称，第 2 个元素是 plotname
                aliasplotname = alias[1]
                alias = alias[0]
                newdct['plotinfo'] = dict(plotname=aliasplotname)

            newcls = type(str(alias), (cls,), newdct)
            clsmodule = sys.modules[cls.__module__]
            setattr(clsmodule, alias, newcls)

        # 返回创建出的类
        return cls

    def donew(cls, *args, **kwargs):
        '''
        拦截实例创建，创建对应实例变量来接管 ``lines`` / ``plotinfo`` / ``plotlines``
        类属性，并为 ``lines`` 及其内部 line 添加 alias。
        '''
        # _obj.plotinfo 会遮蔽类中的 plotinfo 定义
        plotinfo = cls.plotinfo()

        for pname, pdef in cls.plotinfo._getitems():
            setattr(plotinfo, pname, kwargs.pop(pname, pdef))

        # 创建对象并设置参数
        _obj, args, kwargs = super(MetaLineSeries, cls).donew(*args, **kwargs)

        # 设置对象上的 plotinfo 成员
        _obj.plotinfo = plotinfo

        # _obj.lines 会遮蔽类中的 lines 定义
        _obj.lines = cls.lines()

        # _obj.plotlines 会遮蔽类中的 plotlines 定义
        _obj.plotlines = cls.plotlines()

        # 为 lines 和 lines 类本身添加 alias
        _obj.l = _obj.lines
        if _obj.lines.fullsize():
            _obj.line = _obj.lines[0]

        for l, line in enumerate(_obj.lines):
            setattr(_obj, 'line_%s' % l, _obj._getlinealias(l))
            setattr(_obj, 'line_%d' % l, line)
            setattr(_obj, 'line%d' % l, line)

        # 参数值此时已经在 __init__ 前设置完毕
        return _obj, args, kwargs


class LineSeries(with_metaclass(MetaLineSeries, LineMultiple)):
    '''多线序列的基类，用于承载 lines、plotinfo 和 plotlines。'''

    plotinfo = dict(
        plot=True,
        plotmaster=None,
        legendloc=None,
    )

    csv = True

    @property
    def array(self):
        return self.lines[0].array

    def __getattr__(self, name):
        # 对象自身找不到属性时，允许按 line 名称直接引用 line。
        # 如果对象自身设置了同名属性，会在到达这里前被找到。
        return getattr(self.lines, name)

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, key):
        return self.lines[0][key]

    def __setitem__(self, key, value):
        setattr(self.lines, self.lines._getlinealias(key), value)

    def __init__(self, *args, **kwargs):
        # 如果有 args/kwargs 传到这里，说明上游处理有问题。
        # 定义 __init__ 可保证后续 lineiterator 的 findbases 能找到 im_func；
        # object.__init__ 没有 im_func（object 使用 slots）。
        super(LineSeries, self).__init__()
        pass

    def plotlabel(self):
        label = self.plotinfo.plotname or self.__class__.__name__
        sublabels = self._plotlabel()
        if sublabels:
            for i, sublabel in enumerate(sublabels):
                # if isinstance(sublabel, LineSeries): ## 不可用 ???
                if hasattr(sublabel, 'plotinfo'):
                    try:
                        s = sublabel.plotinfo.plotname
                    except:
                        s = ''

                    sublabels[i] = s or sublabel.__name__

            label += ' (%s)' % ', '.join(map(str, sublabels))
        return label

    def _plotlabel(self):
        return self.params._getvalues()

    def _getline(self, line, minusall=False):
        if isinstance(line, string_types):
            lineobj = getattr(self.lines, line)
        else:
            if line == -1:  # 恢复原 API 行为：默认值 -> 0
                if minusall:  # 负数表示所有 line
                    return None
                line = 0
            lineobj = self.lines[line]

        return lineobj

    def __call__(self, ago=None, line=-1):
        '''返回自身的延迟版本，或按 timeframe 适配后的版本。

        Args:
            ago: ``None`` 或 ``LineRoot`` 时返回 ``LinesCoupler``；其他情况按整数处理，
                返回 ``LineDelay``。
            line: 要引用的 line 名称或索引。返回 ``LinesCoupler`` 时，``-1`` 表示适配
                当前 ``LineMultiple`` 对象的全部 line；否则只适配指定 line。返回
                ``LineDelay`` 时，``-1`` 等同于 ``0``，用于保留旧默认行为。

        Returns:
            LinesCoupler | LineDelay: 适配或延迟后的 line 对象。
        '''
        from .lineiterator import LinesCoupler  # 避免循环 import

        if ago is None or isinstance(ago, LineRoot):
            args = [self, ago]
            lineobj = self._getline(line, minusall=True)
            if lineobj is not None:
                args[0] = lineobj

            return LinesCoupler(*args, _ownerskip=self)

        # 其他情况假定 ago 是 int，返回 LineDelay 对象
        return LineDelay(self._getline(line), ago, _ownerskip=self)

    # 下列操作必须覆写，确保子类可以通过 super 访问；super 不会调用 __getattr__，
    # 而下面的 LineSeriesStub 已经使用 super。
    def forward(self, value=NAN, size=1):
        self.lines.forward(value, size)

    def backwards(self, size=1, force=False):
        self.lines.backwards(size, force=force)

    def rewind(self, size=1):
        self.lines.rewind(size)

    def extend(self, value=NAN, size=0):
        self.lines.extend(value, size)

    def reset(self):
        self.lines.reset()

    def home(self):
        self.lines.home()

    def advance(self, size=1):
        self.lines.advance(size)


class LineSeriesStub(LineSeries):
    '''基于单条 line 模拟 ``LineMultiple`` 对象的 stub。

    Args:
        line: 要包装的单条 line。
        slave: 是否作为从属 line 使用。

    Returns:
        LineSeriesStub: 可当作 ``LineSeries`` 使用的单 line 包装对象。

    index 管理操作会考虑该 line 是否为 slave。若不考虑 slave，单独 line 可能被推进
    两次：一次来自 ``LineMultiple`` 推进所有持有 line，另一次来自持有它的对象的常规
    管理。
    '''

    extralines = 1

    def __init__(self, line, slave=False):
        self.lines = self.__class__.lines(initlines=[line])
        # 给外部机会找到 line owner（至少绘图需要）
        self.owner = self._owner = line._owner
        self._minperiod = line._minperiod
        self.slave = slave

    # 只有对象不是 slave 时才执行下列操作
    def forward(self, value=NAN, size=1):
        if not self.slave:
            super(LineSeriesStub, self).forward(value, size)

    def backwards(self, size=1, force=False):
        if not self.slave:
            super(LineSeriesStub, self).backwards(size, force=force)

    def rewind(self, size=1):
        if not self.slave:
            super(LineSeriesStub, self).rewind(size)

    def extend(self, value=NAN, size=0):
        if not self.slave:
            super(LineSeriesStub, self).extend(value, size)

    def reset(self):
        if not self.slave:
            super(LineSeriesStub, self).reset()

    def home(self):
        if not self.slave:
            super(LineSeriesStub, self).home()

    def advance(self, size=1):
        if not self.slave:
            super(LineSeriesStub, self).advance(size)

    def qbuffer(self):
        if not self.slave:
            super(LineSeriesStub, self).qbuffer()

    def minbuffer(self, size):
        if not self.slave:
            super(LineSeriesStub, self).minbuffer(size)


def LineSeriesMaker(arg, slave=False):
    if isinstance(arg, LineSeries):
        return arg

    return LineSeriesStub(arg, slave=slave)
