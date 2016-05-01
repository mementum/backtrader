#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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
from .lineseries import LineSeriesMaker


class MetaIndicator(IndicatorBase.__class__):
    _indcol = dict()

    _icache = dict()

    @classmethod
    def cleancache(cls):
        cls._icache = dict()

    def __call__(cls, *args, **kwargs):
        # implement a cache to avoid duplicating lines actions
        ckey = (cls, tuple(args), tuple(kwargs.items()))  # tuples are hashable
        try:
            return cls._icache[ckey]
        except TypeError:  # something not hashable
            return super(MetaIndicator, cls).__call__(*args, **kwargs)
        except KeyError:
            pass  # hashable but not in the cache

        _obj = super(MetaIndicator, cls).__call__(*args, **kwargs)
        return cls._icache.setdefault(ckey, _obj)

    def __init__(cls, name, bases, dct):
        '''
        Class has already been created ... register subclasses
        '''
        # Initialize the class
        super(MetaIndicator, cls).__init__(name, bases, dct)

        if not cls.aliased and \
           name != 'Indicator' and not name.startswith('_'):
            cls._indcol[name] = cls

    def donew(cls, *args, **kwargs):

        if IndicatorBase.next == cls.next:
            # if next has not been overriden, there is no need for a
            # "once" because the indicator is using indicator composition
            # and line binding avoid calling the one step at a time "next"
            cls.once = cls.once_empty
        else:
            # next overriden. Either once is from Indicator or
            # also overriden -> do nothing
            pass

        if IndicatorBase.prenext == cls.prenext:
            cls.preonce = cls.preonce_empty
        else:
            pass

        _obj, args, kwargs = super(MetaIndicator, cls).donew(*args, **kwargs)

        # If only 1 data was passed and it's multiline, put the 2nd
        # and later lines in the datas array. This allows things like
        # passing a "Stochastic" to a crossover indicator and it will
        # automatically calculate the crossover of %k and %d
        if len(_obj.datas) == 1:
            if _obj.data.size():
                r = range(1, _obj.data.size())
            else:
                r = range(0, _obj.data.lines.extrasize())

            for l in r:
                newdata = LineSeriesMaker(_obj.data.lines[l], slave=True)
                _obj.datas.append(newdata)

        # return the values
        return _obj, args, kwargs


class Indicator(with_metaclass(MetaIndicator, IndicatorBase)):
    _ltype = LineIterator.IndType

    csv = False

    def advance(self, size=1):
        # Need intercepting this call to support datas with
        # different lengths (timeframes)
        if len(self) < len(self._clock):
            self.lines.advance(size=size)

    def preonce_empty(self, start, end):
        return

    def preonce(self, start, end):
        # generic implementation
        for i in range(start, end):
            for data in self.datas:
                data.advance()

            for indicator in self._lineiterators[LineIterator.IndType]:
                indicator.advance()

            self.advance()
            self.prenext()

    def once_empty(self, start, end):
        return

    def once(self, start, end):
        # generic implementation
        for i in range(start, end):
            for data in self.datas:
                data.advance()

            for indicator in self._lineiterators[LineIterator.IndType]:
                indicator.advance()

            self.advance()
            self.next()
