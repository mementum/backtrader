#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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


import six
from six.moves import xrange

from .lineiterator import LineIterator, IndicatorBase


class MetaIndicator(IndicatorBase.__class__):
    _indcol = dict()

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

        # return the values
        return _obj, args, kwargs


class Indicator(six.with_metaclass(MetaIndicator, IndicatorBase)):
    _autoinit = True
    _ltype = LineIterator.IndType

    def advance(self):
        # Need intercepting this call to support datas with
        # different lengths (timeframes)
        if len(self) < len(self._clock):
            self.lines.advance()

    def preonce_empty(self, start, end):
        return

    def preonce(self, start, end):
        # generic implementation
        for i in xrange(start, end):
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
        for i in xrange(start, end):
            for data in self.datas:
                data.advance()

            for indicator in self._lineiterators[LineIterator.IndType]:
                indicator.advance()

            self.advance()
            self.next()
