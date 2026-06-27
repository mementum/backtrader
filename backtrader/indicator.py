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


from .utils.py3 import range, with_metaclass

from .lineiterator import LineIterator, IndicatorBase
from .lineseries import LineSeriesMaker, Lines
from .metabase import AutoInfoClass


class MetaIndicator(IndicatorBase.__class__):
    _refname = '_indcol'
    _indcol = dict()

    _icache = dict()
    _icacheuse = False

    @classmethod
    def cleancache(cls):
        cls._icache = dict()

    @classmethod
    def usecache(cls, onoff):
        cls._icacheuse = onoff

    # object cache 于 2016-08-17 停用。如果对象被另一个对象内部使用，
    # 传递过来的 minperiod 信息会在第 2 次使用时被修改，并影响第 1 次使用

    def __call__(cls, *args, **kwargs):
        if not cls._icacheuse:
            return super(MetaIndicator, cls).__call__(*args, **kwargs)

        # 实现 cache，避免重复创建 lines actions
        ckey = (cls, tuple(args), tuple(kwargs.items()))  # tuples hashable
        try:
            return cls._icache[ckey]
        except TypeError:  # something not hashable
            return super(MetaIndicator, cls).__call__(*args, **kwargs)
        except KeyError:
            pass  # hashable but not in the cache

        _obj = super(MetaIndicator, cls).__call__(*args, **kwargs)
        return cls._icache.setdefault(ckey, _obj)

    def __init__(cls, name, bases, dct):
        '''类已经创建完成，注册其 subclasses。'''
        # 初始化 class
        super(MetaIndicator, cls).__init__(name, bases, dct)

        if not cls.aliased and \
           name != 'Indicator' and not name.startswith('_'):
            refattr = getattr(cls, cls._refname)
            refattr[name] = cls

        # 检查 next 和 once 是否都被覆盖
        next_over = cls.next != IndicatorBase.next
        once_over = cls.once != IndicatorBase.once

        if next_over and not once_over:
            # 未覆盖 once 时，需要移动指针并通过 next 模拟 once
            cls.once = cls.once_via_next
            cls.preonce = cls.preonce_via_prenext
            cls.oncestart = cls.oncestart_via_nextstart


class Indicator(with_metaclass(MetaIndicator, IndicatorBase)):
    _ltype = LineIterator.IndType

    csv = False

    def advance(self, size=1):
        # 需要拦截该调用，以支持不同长度/timeframe 的 datas
        if len(self) < len(self._clock):
            self.lines.advance(size=size)

    def preonce_via_prenext(self, start, end):
        # 当覆盖了 prenext 但未覆盖 preonce 时使用的通用实现
        for i in range(start, end):
            for data in self.datas:
                data.advance()

            for indicator in self._lineiterators[LineIterator.IndType]:
                indicator.advance()

            self.advance()
            self.prenext()

    def oncestart_via_nextstart(self, start, end):
        # nextstart 已被覆盖但 oncestart 未被覆盖时，调用覆盖后的 nextstart
        for i in range(start, end):
            for data in self.datas:
                data.advance()

            for indicator in self._lineiterators[LineIterator.IndType]:
                indicator.advance()

            self.advance()
            self.nextstart()

    def once_via_next(self, start, end):
        # once 未被覆盖时，必须通过 next 执行
        for i in range(start, end):
            for data in self.datas:
                data.advance()

            for indicator in self._lineiterators[LineIterator.IndType]:
                indicator.advance()

            self.advance()
            self.next()


class MtLinePlotterIndicator(Indicator.__class__):
    def donew(cls, *args, **kwargs):
        lname = kwargs.pop('name')
        name = cls.__name__

        lines = getattr(cls, 'lines', Lines)
        cls.lines = lines._derive(name, (lname,), 0, [])

        plotlines = AutoInfoClass
        newplotlines = dict()
        newplotlines.setdefault(lname, dict())
        cls.plotlines = plotlines._derive(name, newplotlines, [], recurse=True)

        # 创建对象并设置 params
        _obj, args, kwargs =  \
            super(MtLinePlotterIndicator, cls).donew(*args, **kwargs)

        _obj.owner = _obj.data.owner._clock
        _obj.data.lines[0].addbinding(_obj.lines[0])

        # 将对象和参数返回给调用链
        return _obj, args, kwargs


class LinePlotterIndicator(with_metaclass(MtLinePlotterIndicator, Indicator)):
    pass
