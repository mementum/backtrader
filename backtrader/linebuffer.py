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
import array
import collections
import datetime
import itertools

NAN = float('NaN')


class LineBuffer(object):
    DefaultTypeCode = 'd'

    def __new__(cls, *args, **kwargs):
        typecode = kwargs.get('typecode', cls.DefaultTypeCode)

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
        self.bindings = list()
        self.typecode = typecode
        self.reset()

    def reset(self):
        self.create_array()
        self.idx = -1
        self.extension = 0

    def create_array(self):
        raise NotImplementedError

    def __len__(self):
        return self.idx + 1

    def buflen(self):
        return len(self.array) - self.extension

    def __getitem__(self, ago):
        return self.array[self.idx - ago]

    def get(self, ago=0, size=1):
        return self.array[self.idx - ago - size + 1:self.idx - ago + 1]

    def getzero(self, idx=0, size=1):
        return self.array[idx:idx + size]

    def __setitem__(self, ago, value):
        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def home(self):
        self.idx = -1

    def forward(self, value=NAN, size=1):
        self.idx += size
        for i in xrange(size):
            self.array.append(value)

    def rewind(self, size=1):
        self.idx -= size
        for i in xrange(size):
            self.array.pop()

    def advance(self, size=1):
        self.idx += size

    def extend(self, value=NAN, size=0):
        self.extension += size
        for i in xrange(size):
            self.array.append(value)

    def addbinding(self, binding):
        self.bindings.append(binding)

    def plot(self, idx=0, size=None):
        return self.getzero(idx, size if size is not None else len(self))


class LineBufferArray(LineBuffer):
    def create_array(self):
        self.array = array.array(self.typecode)


class LineBufferList(LineBuffer):
    def create_array(self):
        self.array = list()


class LineBufferDeque(LineBuffer):
    def create_array(self):
        self.array = collections.deque()

    def get(self, ago=0, size=1):
        return list(itertools.islice(self.array, self.idx - ago - size + 1, self.idx - ago + 1))

    def getzero(self, idx=0, size=1):
        return list(itertools.islice(self.array, idx, idx + size))
