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
'''

.. module:: linebuffer

Classes that hold the buffer for a *line* and can operate on it
with appends, forwarding, rewinding, resetting and other

.. moduleauthor:: Daniel Rodriguez


'''
from __future__ import absolute_import, division, print_function, unicode_literals

import array
import collections
import datetime
import itertools

NAN = float('NaN')


class LineBuffer(object):
    ''' Line buffer abstract implementation

    Attributes:
        bindings (list): holds bindings to other lines
            ie: upon getting a value written it will be copied to that other line

        idx (int): actual index where data is store read when *0* is passed
            extension (int): extra room at the end of the buffer to allow lookahead operations

    .. note:: Notes

        The implementation uses an *index 0* approach as follows:
            - 0 is always the insertion point. If idx is 5, any reference to 0 using for example
                __getitem__ (or the [] operator) will be done on position 5 of the buffer

            - This allows to remain Pythonic when addressing array positions, because
              *index -1* returns the "last" value before the current one. Because
              the current one is *index 0*, a reference to -1 will return what's in position 4.

        And so on with -2, -3.
    '''

    DefaultTypeCode = 'd'

    def __new__(cls, *args, **kwargs):
        ''' Upon instance creation selects the appropriate subclass to return

        Upon instantiation and using *typecode* the right subclass is chosen
        for the passed 'typecode'

        Because the returned object is a subclass, __init__ has to be explicitly
        invoked (the standard Python instance creation mechanism has been
        circumvented)

        Keyword Args:
            typecode (str): type of data hold at each point of the line
                'd' for double - the array will be an array.array
                'dq' meant for datetime objects  - the array will be a collections.deque
                'ls' meant for datetime objects  - the array will be a list
        '''
        typecode = kwargs.pop('typecode', cls.DefaultTypeCode)

        if typecode == 'dq':
            newcls = LineBufferDeque
        elif typecode == 'ls':
            newcls = LineBufferList
        else:
            newcls = LineBufferArray

        obj = super(LineBuffer, newcls).__new__(newcls, *args, **kwargs)
        obj.__init__(*args, **kwargs)
        return obj

    def __init__(self, typecode=DefaultTypeCode):
        '''
        Keyword Args:
            typecode (str): type of data hold at each point of the line
                'd' for double - the array will be an array.array
                'dq' meant for datetime objects  - the array will be a collections.deque
                'ls' meant for datetime objects  - the array will be a list
        '''

        self.bindings = list()
        self.typecode = typecode
        self.reset()

    def reset(self):
        ''' Resets the internal buffer structure and the indices
        '''
        self.create_array()
        self.idx = -1
        self.extension = 0

    def create_array(self):
        ''' Actual internal buffer creation. Must be implemented by subclasses
        '''
        raise NotImplementedError

    def __len__(self):
        return self.idx + 1

    def buflen(self):
        ''' Real data that can be currently held in the internal buffer

        The internal buffer can be longer than the actual stored data to allow for "lookahead"
        operations. The real amount of data that is held/can be held in the buffer
        is returned
        '''
        return len(self.array) - self.extension

    def __getitem__(self, ago):
        return self.array[self.idx + ago]

    def get(self, ago=0, size=1):
        ''' Returns a slice of the array relative to *ago*

        Keyword Args:
            ago (int): Point of the array to which size will be added to return the slice
            size(int): size of the slice to return, can be positive or negative

        If size is positive *ago* will mark the end of the iterable and vice versa if size
        is negative

        Returns:
            A slice of the underlying buffer
        '''
        return self.array[self.idx + ago - size + 1:self.idx + ago + 1]

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
            ago (int): Point of the array to which size will be added to return the slice
            value (variable): value to be set
        '''
        self.array[self.idx + ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        ''' Sets a value at position "ago" and executes any associated bindings

        Keyword Args:
            value (variable): value to be set
            ago (int): Point of the array to which size will be added to return the slice
        '''
        self.array[self.idx + ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def home(self):
        ''' Rewinds the logical index to the beginning

        The underlying buffer remains untouched and the actual len can be found out with buflen
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
            size (int): How many extra positions to rewind and reduce the buffer
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

        The purpose is to allow for lookahead operations or to be able to set values
        in the buffer "future"
        '''
        self.extension += size
        for i in range(size):
            self.array.append(value)

    def addbinding(self, binding):
        ''' Adds another line binding

        Keyword Args:
            binding (LineBuffer): another line that must be set when this line becomes a value
        '''
        self.bindings.append(binding)

    def plot(self, idx=0, size=None):
        ''' Returns a slice of the array relative to the real zero of the buffer

        Keyword Args:
            idx (int): Where to start relative to the real start of the buffer
            size(int): size of the slice to return

        This is a variant of getzero which unless told otherwise returns the entire buffer, which
        is usually the idea behind plottint (all must plotted)

        Returns:
            A slice of the underlying buffer
        '''
        return self.getzero(idx, size or len(self))

    def oncebinding(self):
        larray = self.array
        blen = self.buflen()
        for binding in self.bindings:
            binding.array[0:blen] = larray[0:blen]


class LineBufferArray(LineBuffer):
    ''' Line buffer concrete implementation with array.array
    '''
    def __init__(self, typecode='d'):
        super(LineBufferArray, self).__init__(typecode=typecode)

    def create_array(self):
        ''' Instantiates the internal array to array.array
        '''
        # str needed for Python 2/3 bytes/unicode compatibility
        self.array = array.array(str(self.typecode))


class LineBufferList(LineBuffer):
    ''' Line buffer concrete implementation with list
    '''
    def __init__(self, typecode='ls'):
        super(LineBufferArray, self).__init__(typecode=typecode)

    def create_array(self):
        ''' Instantiates the internal array to list
        '''
        self.array = list()


class LineBufferDeque(LineBuffer):
    ''' Line buffer concrete implementation with collections.deque

    Some work is needed with get and getzero to return slices, because
    collections.deque has no direct support
    '''
    def __init__(self, typecode='dq'):
        super(LineBufferDeque, self).__init__(typecode=typecode)

    def create_array(self):
        ''' Instantiates the internal array to list
        '''
        self.array = collections.deque()

    def get(self, ago=0, size=1):
        ''' Specialized implementation using itertools.islice. No behavior changes
        '''
        # Need to return a list because the return value may be reused several times
        return list(itertools.islice(self.array, self.idx + ago - size + 1, self.idx + ago + 1))

    def getzero(self, idx=0, size=1):
        ''' Specialized implementation using itertools.islice. No behavior changes
        '''
        # Need to return a list because the return value may be reused several times
        return list(itertools.islice(self.array, idx, idx + size))
