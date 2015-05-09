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

.. module:: linebuffer

Classes that hold the buffer for a *line* and can operate on it
with appends, forwarding, rewinding, resetting and other

.. moduleauthor:: Daniel Rodriguez

'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import array

import six
from six.moves import xrange

from .lineroot import LineRoot, LineSingle
from . import metabase
from .utils import num2date, cmp


NAN = float('NaN')


class LineBuffer(LineSingle):
    '''
    LineBuffer defines an interface to an "array.array" (or list) in which
    index 0 points to the item which is active for input and output.

    Positive indices fetch values from the past (left hand side)
    Negative indices fetch values from the future (if the array has been
    extended on the right hand side)

    With this behavior no index has to be passed around to entities which have
    to work with the current value produced by other entities: the value is
    always reachable at "0".

    Likewise storing the current value produced by "self" is done at 0.

    Additional operations to move the pointer (home, forward, extend, rewind,
    advance getzero) are provided

    The class can also hold "bindings" to other LineBuffers. When a value
    is set in this class
    it will also be set in the binding.
    '''

    def __init__(self, typecode='d'):
        '''
        Keyword Args:
            typecode (str): type of data hold at each point of the line
                'd' for double - the array will be an array.array
                'ls' meant for datetime objects  - the array will be a list
        '''
        self.typecode = typecode
        self.bindings = list()
        self.reset()

    def reset(self):
        ''' Resets the internal buffer structure and the indices
        '''
        self.create_array()
        self.idx = -1
        self.extension = 0

    def create_array(self):
        self.array = array.array(str(self.typecode))

    def __len__(self):
        return self.idx + 1

    def buflen(self):
        ''' Real data that can be currently held in the internal buffer

        The internal buffer can be longer than the actual stored data to
        allow for "lookahead" operations. The real amount of data that is
        held/can be held in the buffer
        is returned
        '''
        return len(self.array) - self.extension

    def __getitem__(self, ago):
        return self.array[self.idx - ago]

    def get(self, ago=0, size=1):
        ''' Returns a slice of the array relative to *ago*

        Keyword Args:
            ago (int): Point of the array to which size will be added
            to return the slice size(int): size of the slice to return,
            can be positive or negative

        If size is positive *ago* will mark the end of the iterable and vice
        versa if size is negative

        Returns:
            A slice of the underlying buffer
        '''
        return self.array[self.idx - ago - size + 1:self.idx - ago + 1]

    def getzero(self, idx=0, size=1):
        ''' Returns a slice of the array relative to the real zero of the buffer

        Keyword Args:
            idx (int): Where to start relative to the real start of the buffer
            size(int): size of the slice to return

        Returns:
            A slice of the underlying buffer
        '''
        return self.array[idx:idx + size]

    def __setitem__(self, ago, value):
        ''' Sets a value at position "ago" and executes any associated bindings

        Keyword Args:
            ago (int): Point of the array to which size will be added to return
            the slice
            value (variable): value to be set
        '''
        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        ''' Sets a value at position "ago" and executes any associated bindings

        Keyword Args:
            value (variable): value to be set
            ago (int): Point of the array to which size will be added to return
            the slice
        '''
        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def home(self):
        ''' Rewinds the logical index to the beginning

        The underlying buffer remains untouched and the actual len can be found
        out with buflen
        '''
        self.idx = -1

    def forward(self, value=NAN, size=1):
        ''' Moves the logical index foward and enlarges the buffer as much as needed

        Keyword Args:
            value (variable): value to be set in new positins
            size (int): How many extra positions to enlarge the buffer
        '''
        self.idx += size
        for i in range(size):
            self.array.append(value)

    def rewind(self, size=1):
        ''' Moves the logical index backwards and reduces the buffer as much as needed

        Keyword Args:
            size (int): How many extra positions to rewind and reduce the
            buffer

        '''
        self.idx -= size
        for i in range(size):
            self.array.pop()

    def advance(self, size=1):
        ''' Advances the logical index without touching the underlying buffer

        Keyword Args:
            size (int): How many extra positions to move forward
        '''
        self.idx += size

    def extend(self, value=NAN, size=0):
        ''' Extends the underlying array with positions that the index will not reach

        Keyword Args:
            value (variable): value to be set in new positins
            size (int): How many extra positions to enlarge the buffer

        The purpose is to allow for lookahead operations or to be able to
        set values in the buffer "future"
        '''
        self.extension += size
        for i in range(size):
            self.array.append(value)

    def addbinding(self, binding):
        ''' Adds another line binding

        Keyword Args:
            binding (LineBuffer): another line that must be set when this line
            becomes a value
        '''
        self.bindings.append(binding)
        # record in the binding when the period is starting (never sooner
        # than self)
        binding.updateminperiod(self._minperiod)

    def plot(self, idx=0, size=None):
        ''' Returns a slice of the array relative to the real zero of the buffer

        Keyword Args:
            idx (int): Where to start relative to the real start of the buffer
            size(int): size of the slice to return

        This is a variant of getzero which unless told otherwise returns the
        entire buffer, which is usually the idea behind plottint (all must
        plotted)

        Returns:
            A slice of the underlying buffer
        '''
        return self.getzero(idx, size or len(self))

    def oncebinding(self):
        '''
        Executes the bindings when running in "once" mode
        '''
        larray = self.array
        blen = self.buflen()
        for binding in self.bindings:
            binding.array[0:blen] = larray[0:blen]

    def bind2lines(self, binding=0):
        '''
        Stores a binding to another line. "binding" can be an index or a name
        '''
        if isinstance(binding, six.string_types):
            line = getattr(self._owner.lines, binding)
        else:
            line = self._owner.lines[binding]

        self.addbinding(line)

        return self

    bind2line = bind2lines

    def __call__(self, ago=0):
        '''
        Return a delayed version of self by "ago" periods
        '''
        return LineDelay(self, ago)

    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        return LinesOperation(self, other, operation, r=r,
                              _ownerskip=_ownerskip)

    def _makeoperationown(self, operation, _ownerskip=None):
        return LineOwnOperation(self, operation, _ownerskip=None)

    def datetime(self, ago=0):
        return num2date(self.array[self.idx - ago])

    def date(self, ago=0):
        return self.datetime(ago).date()

    def time(self, ago=0):
        return self.datetime(ago).time()


class MetaLineActions(LineBuffer.__class__):
    '''
    Metaclass for Lineactions

    Scans the instance before init for LineBuffer (or parentclass LineSingle)
    instances to calculate the minperiod for this instance

    postinit it registers the instance to the owner (remember that owner has
    been found in the base Metaclass for LineRoot)
    '''
    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineActions, cls).dopreinit(_obj,
                                                  *args,
                                                  **kwargs)

        # Do not produce anything until the operation lines produce something
        _minperiod = \
            max([x._minperiod for x in args if isinstance(x, LineSingle)])

        # update own minperiod if needed
        _obj.updateminperiod(_minperiod)

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineActions, cls).dopostinit(_obj, *args, **kwargs)

        # register with _owner to be kicked later
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


class LineActions(six.with_metaclass(MetaLineActions, LineBuffer)):
    '''
    Base class derived from LineBuffer intented to defined the
    minimum interface to make it compatible with a LineIterator by
    providing operational _next and _once interfaces.

    The metaclass does the dirty job of calculating minperiods and registering
    '''

    _ltype = LineBuffer.IndType

    @staticmethod
    def arrayize(obj):
        if isinstance(obj, LineRoot):
            if not isinstance(obj, LineSingle):
                obj = obj[0]  # get 1st line from multiline
        else:
            obj = PseudoArray(obj)

        return obj

    def _next(self):
        clock_len = len(self._owner)
        if clock_len > len(self):
            self.forward()

        if clock_len > self._minperiod:
            self.next()
        elif clock_len == self._minperiod:
            # only called for the 1st value
            self.nextstart()
        else:
            self.prenext()

    def _once(self):
        self.forward(size=self._owner.buflen())
        self.home()

        self.preonce(0, self._minperiod - 1)
        self.oncestart(self._minperiod - 1, self._minperiod)
        self.once(self._minperiod, self.buflen())

        self.oncebinding()


class LineDelay(LineActions):
    '''
    Takes a LineBuffer (or derived) object and stores the value from
    "ago" periods effectively delaying the delivery of data
    '''
    def __init__(self, a, ago):
        super(LineDelay, self).__init__()
        self.a = a
        self.ago = ago

        # Need to add the delay to the period. "ago" is 0 based and therefore
        # we need to pass and extra 1 which is the minimum defined period for
        # any data (which will be substracted inside addminperiod)
        self.addminperiod(ago + 1)

    def next(self):
        self[0] = self.a[self.ago]

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        src = self.a.array
        ago = self.ago

        for i in xrange(start, end):
            dst[i] = src[i - ago]


class LinesOperation(LineActions):
    '''
    Holds an operation that operates on a two operands. Example: mul

    It will "next"/traverse the array applying the operation on the
    two operands and storing the result in self.

    To optimize the operations and avoid conditional checks the right
    next/once is chosen using the operation direction (normal or reversed)
    and the nature of the operands (LineBuffer vs non-LineBuffer)

    In the "once" operations "map" could be used as in:

        operated = map(self.operation, srca[start:end], srcb[start:end])
        self.array[start:end] = array.array(str(self.typecode), operated)

    No real execution time benefits were appreciated and therefore the loops
    have been kept in place for clarity (although the maps are not really
    unclear here)
    '''
    def __init__(self, a, b, operation, r=False):
        super(LinesOperation, self).__init__()

        self.operation = operation
        self.a = a  # always a linebuffer
        self.b = b

        if not isinstance(b, LineBuffer):
            self.next = self._next_val_op if not r else self._next_val_op_r
            self.once = self._once_val_op if not r else self._once_val_op_r

        if r:
            self.a, self.b = b, a

    def next(self):
        self[0] = self.operation(self.a[0], self.b[0])

    def _next_val_op(self):
        self[0] = self.operation(self.a[0], self.b)

    def _next_val_op_r(self):
        self[0] = self.operation(self.a, self.b[0])

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        op = self.operation

        for i in xrange(start, end):
            dst[i] = op(srca[i], srcb[i])

    def _once_val_op(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b
        op = self.operation

        for i in xrange(start, end):
            dst[i] = op(srca[i], srcb)

    def _once_val_op_r(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a
        srcb = self.b.array
        op = self.operation

        for i in xrange(start, end):
            dst[i] = op(srca, srcb[i])


class LineOwnOperation(LineActions):
    '''
    Holds an operation that operates on a single operand. Example: abs

    It will "next"/traverse the array applying the operation and storing
    the result in self
    '''
    def __init__(self, a, operation):
        super(LineOwnOperation, self).__init__()

        self.operation = operation
        self.a = a

    def next(self):
        self[0] = self.operation(self.a[0])

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        op = self.operation

        for i in xrange(start, end):
            dst[i] = op(srca[i])


class Logic(LineActions):
    def __init__(self, a, b):
        super(Logic, self).__init__()

        self.a = self.arrayize(a)
        self.b = self.arrayize(b)


class If(Logic):
    def __init__(self, cond, a, b):
        super(If, self).__init__(a, b)

        self.cond = self.arrayize(cond)

    def next(self):
        self[0] = self.a[0] if self.cond[0] else self.b[0]

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        cond = self.cond.array

        for i in xrange(start, end):
            dst[i] = srca[i] if cond[i] else srcb[i]


class And(Logic):
    def __init__(self, a, b):
        super(And, self).__init__(a, b)

    def next(self):
        self[0] = self.a[0] and self.b[0]

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array

        for i in xrange(start, end):
            dst[i] = srca[i] and srcb[i]


class Or(Logic):
    def __init__(self, a, b):
        super(Or, self).__init__(a, b)

    def next(self):
        self[0] = self.a[0] or self.b[0]

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array

        for i in xrange(start, end):
            dst[i] = srca[i] or srcb[i]


class Cmp(Logic):
    def __init__(self, a, b):
        super(Cmp, self).__init__(a, b)

    def next(self):
        self[0] = cmp(self.a[0], self.b[0])

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array

        for i in xrange(start, end):
            dst[i] = cmp(srca[i], srcb[i])
