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
import datetime


MAXLEN = 1024
NAN = float('NaN')


class LineBufferBase(object):
    DEFVALUE = NAN
    BUFSIZE = 0

    def __init__(self):
        self.reset()
        self.bindings = list()

    def reset(self):
        self.array = array.array('f', [self.DEFVALUE] * self.BUFSIZE)
        self.idx = -1

    def __len__(self):
        return self.idx + 1

    def buflen(self):
        return len(self.array)

    def __call__(self, ago=0, size=1):
        return self.get(ago, size)

    def __getitem__(self, ago):
        raise NotImplementedError

    def get(self, ago=0, size=1):
        return [self[x] for x in xrange(ago + size - 1, ago - 1, -1)]

    def getzero(self, idx=0, size=1):
        return self.array[idx:idx + size]

    def __setitem__(self, ago, value):
        raise NotImplementedError

    def set(self, value, ago=0):
        self[ago] = value

    def home(self):
        self.idx = -1

    def forward(self, value=NAN):
        raise NotImplementedError

    def advance(self):
        self.idx += 1

    def date(self, ago=0):
        return datetime.date.fromordinal(int(self[ago]))

    def setdate(self, value, ago=0):
        if isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
            value = value.toordinal()

        self[ago] = value

    def time(self, ago=0):
        hm, s = divmod(int(self[ago]), 60)
        h, m = divmod(hm, 60)
        return datetime.time(h, m, s)

    def settime(self, value, ago=0):
        if isinstance(value, datetime.timedelta):
            value = value.seconds
        elif isinstance(value, datetime.time):
            value = value.second + value.minute * 60 + value.hour * 3600

        self[ago] = value

    def linedate(self):
        raise NotImplementedError

    def linetime(self):
        raise NotImplementedError

    def addbinding(self, binding):
        self.bindings.append(binding)


class LineBufferFull(LineBufferBase):

    def __getitem__(self, ago):
        return self.array[self.idx - ago]

    def get(self, ago=0, size=1):
        return self.array[self.idx - ago - size + 1:self.idx - ago + 1]

    def __setitem__(self, ago, value):
        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def forward(self, value=NAN):
        self.idx += 1
        self.array.append(value)

    def linedate(self):
        return LineBufferFullDate()

    def linetime(self):
        return LineBufferFullTime()


class LineBufferFullDate(LineBufferFull):
    def __getitem__(self, ago):
        value = self.array[self.idx - ago]
        return datetime.date.fromordinal(int(value))

    def get(self, ago=0, size=1):
        return [self[x] for x in xrange(ago + size - 1, ago - 1, -1)]

    def __setitem__(self, ago, value):
        if isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
            value = value.toordinal()

        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        if isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
            value = value.toordinal()

        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value


class LineBufferFullTime(LineBufferFull):
    def __getitem__(self, ago):
        value = self.array[self.idx - ago]
        hm, s = divmod(int(value), 60)
        h, m = divmod(hm, 60)
        return datetime.time(h, m, s)

    def get(self, ago=0, size=1):
        return [self[x] for x in xrange(ago + size - 1, ago - 1, -1)]

    def __setitem__(self, ago, value):
        if isinstance(value, datetime.timedelta):
            value = value.seconds
        elif isinstance(value, datetime.time):
            value = value.second + value.minute * 60 + value.hour * 3600

        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value

    def set(self, value, ago=0):
        if isinstance(value, datetime.timedelta):
            value = value.seconds
        elif isinstance(value, datetime.time):
            value = value.second + value.minute * 60 + value.hour * 3600

        self.array[self.idx - ago] = value
        for binding in self.bindings:
            binding[ago] = value


class LineBufferRing(LineBufferBase):
    BUFSIZE = MAXLEN

    def __getitem__(self, ago):
        return self.array[(self.idx - ago) % self.BUFSIZE]

    def __setitem__(self, ago, value):
        self.array[(self.idx - ago) % self.BUFSIZE] = value

    def forward(self, value=NAN):
        self.idx += 1
        self.array[self.idx % self.BUFSIZE] = value

    def linedate(self):
        return LineBufferRingDate()

    def linetime(self):
        return LineBufferRingTime()


class LineBufferRingDate(LineBufferRing):
    def __getitem__(self, ago):
        value = self.array[(self.idx - ago) % self.BUFSIZE]
        return datetime.date.fromordinal(int(value))


class LineBufferRingTime(LineBufferRing):
    def __getitem__(self, ago):
        value = self.array[(self.idx - ago) % self.BUFSIZE]
        hm, s = divmod(int(value), 60)
        h, m = divmod(hm, 60)
        return datetime.time(h, m, s)
