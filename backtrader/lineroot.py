#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################

from __future__ import absolute_import, division, print_function, unicode_literals

import operator

import six

from . import metabase


class MetaLineRoot(metabase.MetaParams):
    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineRoot, cls).donew(*args, **kwargs)

        # Find the owner and store it
        # startlevel = 4 ... to skip intermediate call stacks
        ownerskip = kwargs.pop('_ownerskip', None)
        _obj._owner = metabase.findowner(_obj, _obj._OwnerCls or LineMultiple, skip=ownerskip)

        # Parameter values have now been set before __init__
        return _obj, args, kwargs


class LineRoot(six.with_metaclass(MetaLineRoot, object)):
    _OwnerCls = None
    _minperiod = 1

    IndType, StratType, ObsType = range(3)

    def setminperiod(self, minperiod):
        self._minperiod = minperiod

    def updateminperiod(self, minperiod):
        self._minperiod = max(self._minperiod, minperiod)

    def addminperiod(self, minperiod):
        raise NotImplementedError

    def prenext(self):
        pass

    def nextstart(self):
        self.next()

    def next(self):
        pass

    def preonce(self, start, end):
        pass

    def oncestart(self, start, end):
        self.once(start, end)

    def ocne(self, start, end):
        pass

    def _roperation(self, other, operation):
        return self._operation(other, operation, r=True)

    def __add__(self, other):
        return self._operation(other, operator.add)

    def __radd__(self, other):
        return self._roperation(other, operator.add)

    def __sub__(self, other):
        return self._operation(other, operator.sub)

    def __rsub__(self, other):
        return self._roperation(other, operator.sub)

    def __mul__(self, other):
        return self._operation(other, operator.mul)

    def __rmul__(self, other):
        return self._roperation(other, operator.mul)

    def __truediv__(self, other):
        return self._operation(other, operator.truediv)

    def __rtruediv__(self, other):
        return self._roperation(other, operator.truediv)

    def __pow__(self, other):
        return self._operation(other, operator.pow)

    def __rpow__(self, other):
        return self._roperation(other, operator.pow)

    def __abs__(self):
        return self._operationown(operator.abs)


class LineMultiple(LineRoot):
    def addminperiod(self, minperiod):
        # pass it down to the lines
        for line in self.lines:
            line.addminperiod(minperiod)


class LineSingle(LineRoot):
    def addminperiod(self, minperiod):
        # Discard 1 which is the minimum period and would only be a carry over
        self._minperiod += minperiod - 1
