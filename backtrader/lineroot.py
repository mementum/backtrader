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
'''

.. module:: lineroot

Definition of the base class LineRoot and base classes LineSingle/LineMultiple
to define interfaces and hierarchy for the real operational classes

.. moduleauthor:: Daniel Rodriguez

'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import operator

import six

from . import metabase


class MetaLineRoot(metabase.MetaParams):
    '''
    Once the object is created (effectively pre-init) the "owner" of this
    class is sought
    '''

    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineRoot, cls).donew(*args, **kwargs)

        # Find the owner and store it
        # startlevel = 4 ... to skip intermediate call stacks
        ownerskip = kwargs.pop('_ownerskip', None)
        _obj._owner = metabase.findowner(_obj,
                                         _obj._OwnerCls or LineMultiple,
                                         skip=ownerskip)

        # Parameter values have now been set before __init__
        return _obj, args, kwargs


class LineRoot(six.with_metaclass(MetaLineRoot, object)):
    '''
    Defines a common base and interfaces for Single and Multiple
    LineXXX instances

        Period management
        Iteration management
        Operation (dual/single operand) Management
        Rich Comparison operator definition
    '''
    _OwnerCls = None
    _minperiod = 1

    IndType, StratType, ObsType = range(3)

    def _stage2(self):
        # change to real comparison function
        self._operation = self._operation_stage2
        self._comparison = self._operation_stage2
        self._operationown = self._operationown_stage2

    def setminperiod(self, minperiod):
        '''
        Direct minperiod manipulation. It could be used for example
        by a strategy
        to not wait for all indicators to produce a value
        '''
        self._minperiod = minperiod

    def updateminperiod(self, minperiod):
        '''
        Update the minperiod if needed. The minperiod will have been
        calculated elsewhere
        and has to take over if greater that self's
        '''
        self._minperiod = max(self._minperiod, minperiod)

    def addminperiod(self, minperiod):
        '''
        Add a minperiod to own ... to be defined by subclasses
        '''
        raise NotImplementedError

    def prenext(self):
        '''
        It will be called during the "minperiod" phase of an iteration.
        '''
        pass

    def nextstart(self):
        '''
        It will be called when the minperiod phase is over for the 1st
        post-minperiod value. Only called once and defaults to automatically
        calling next
        '''
        self.next()

    def next(self):
        '''
        Called to calculate values when the minperiod is over
        '''
        pass

    def preonce(self, start, end):
        '''
        It will be called during the "minperiod" phase of a "once" iteration
        '''
        pass

    def oncestart(self, start, end):
        '''
        It will be called when the minperiod phase is over for the 1st
        post-minperiod value

        Only called once and defaults to automatically calling once
        '''
        self.once(start, end)

    def once(self, start, end):
        '''
        Called to calculate values at "once" when the minperiod is over
        '''
        pass

    # Arithmetic operators
    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        raise NotImplementedError

    def _makeoperationown(self, operation, _ownerskip=None):
        raise NotImplementedError

    def _operationown(self, operation):
        '''
        To be defined by subclasses to implement an operation on "self"
        '''
        raise NotImplementedError

    def _operation(self, other, operation, r=False, intify=False):
        '''
        To be defined by subclasses to implement an operation on "self"
        and "other" with "operation"

        If "r" is True is a reverse operation
        '''
        raise NotImplementedError

    def _roperation(self, other, operation, intify=False):
        '''
        Relies on self._operation to and passes "r" True to define a
        reverse operation
        '''
        return self._operation(other, operation, r=True, intify=intify)

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

    # Comparison operators
    def _comparison(self, other, operation):
        raise NotImplementedError

    def __lt__(self, other):
        return self._comparison(other, operator.__lt__)

    def __gt__(self, other):
        return self._comparison(other, operator.__gt__)

    def __le__(self, other):
        return self._comparison(other, operator.__le__)

    def __ge__(self, other):
        return self._comparison(other, operator.__ge__)

    def __eq__(self, other):
        return self._comparison(other, operator.__eq__)

    def __ne__(self, other):
        return self._comparison(other, operator.__ne__)


class LineMultiple(LineRoot):
    '''
    Base class for LineXXX instances that hold more than one line
    '''
    def _stage2(self):
        super(LineMultiple, self)._stage2()
        for line in self.lines:
            line._stage2()

    def addminperiod(self, minperiod):
        '''
        The passed minperiod is fed to the lins
        '''
        # pass it down to the lines
        for line in self.lines:
            line.addminperiod(minperiod)

    def _operationown(self, operation):
        '''
        Operation with single operand which is "self"
        '''
        return self.lines[0]._makeoperationown(operation, _ownerskip=self)

    def _operationown_stage2(self, operation):
        return operation(self[0][0])

    def _operation(self, other, operation, r=False, intify=False):
        '''
        Operation for two operands. Examines other and decides if other or
        items of it will be part of the operation

        "self" will be skipped as potential owner for the resulting
        operation, because the owner is also a LineMultiple instance,
        but's for sure not the one taking part in the comparison
        '''
        if isinstance(other, LineMultiple):
            # FIXME: ideally return a LineSeries object at least as long as the
            # smallest size of both operands
            return self.lines[0]._makeoperation(other.lines[0],
                                                operation,
                                                r,
                                                _ownerskip=self)
        elif isinstance(other, LineSingle):
            return self.lines[0]._makeoperation(other,
                                                operation,
                                                r,
                                                _ownerskip=self)

        # assume other is a standard type
        return self.lines[0]._makeoperation(other,
                                            operation,
                                            r,
                                            _ownerskip=self)

    _comparison = _operation

    def _operation_stage2(self, other, operation):
        '''
        Rich Comparison operators. Scans other and returns either an operation
        with other directly or a subitem from other
        '''
        if isinstance(other, LineRoot):
            # either operation(LineBuffer, LineBuffer) or
            # operation(LineBuffer, float) both are defined by LineBuffer
            return operation(self.lines[0], other[0])

        # operation(float, other) ... expecting other to be a float
        return operation(self.lines[0][0], other)


class LineSingle(LineRoot):
    '''
    Base class for LineXXX instances that hold a single line
    '''
    def addminperiod(self, minperiod):
        '''
        Add the minperiod (substracting the overlapping 1 minimum period)
        '''
        self._minperiod += minperiod - 1

    def _operationown(self, operation):
        '''
        Operation with single operand which is "self"
        '''
        return self._makeoperationown(operation)

    def _operationown_stage2(self, operation):
        return operation(self[0])

    def _operation(self, other, operation, r=False, intify=False):
        '''
        Two operands' operation. Scanning of other happens to understand
        if other must be directly an operand or rather a subitem thereof
        '''
        if False:
            if isinstance(other, LineRoot):
                if not isinstance(other, LineSingle):
                    # This forces calling other's reverse operation
                    return NotImplemented

        if isinstance(other, LineMultiple):
            return self._makeoperation(other.lines[0], operation, r)

        return self._makeoperation(other, operation, r)

    _comparison = _operation

    def _operation_stage2(self, other, operation):
        '''
        Rich Comparison operators. Scans other and returns either an
        operation with other directly or a subitem from other
        '''
        if isinstance(other, LineMultiple):
            # operation(float, float)
            return operation(self[0], other[0][0])
        elif isinstance(other, LineSingle):
            # operation(float, float)
            return operation(self[0], other[0])

        # operation(float, other) ... expecting other to be a float

        # if LineMultiple is not caught above then
        # if other is LineMultiple then operation(float, LineMultiple), which
        # triggers the reverse operation(float, float) in LineMultiple
        # maybe too many indirections
        return operation(self[0], other)
