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
import datetime
import itertools

from .. import dataseries
from .. import linebuffer


class MyCSV1(dataseries.OHLCDateTime):

    def __init__(self, path):
        self.path = path
        self.f = None

    def getdata(self):
        return self

    def start(self):
        self.reset()

        try:
            self.f = open(self.path, 'rb')
        except IOError:
            self.f = None
        else:
            # skip the headers line
            self.f.readline()

    def next(self):
        if self.f is None:
            return False

        try:
            line = self.f.readline()
        except (IOError, ValueError,):
            self.f.close()
            self.f = None
            return False

        if not line:
            return False

        linetokens = line.rstrip('\r\n').split(',')

        self.forward() # advance data pointer
        i = itertools.count(0)
        i.next() # skip ticker name
        isday = linetokens[i.next()] == 'D'
        dttxt = linetokens[i.next()]
        y, m, d = int(dttxt[0:4]), int(dttxt[4:6]), int(dttxt[6:8])
        self.lines.date = datetime.date(y, m, d).toordinal()

        tmtxt = linetokens[i.next()]
        if not isday:
            hh, mm, ss = int(tmtxt[0:2]), int(tmtxt[2:4]), int(tmtxt[4:6])
            self.lines.time = hh * 60 * 60 + mm * 60 + ss
        else:
            self.lines.time = 0

        self.lines.open = float(linetokens[i.next()])
        self.lines.high = float(linetokens[i.next()])
        self.lines.low = float(linetokens[i.next()])
        self.lines.close = float(linetokens[i.next()])
        self.lines.volume = float(linetokens[i.next()])
        self.lines.openinterest = float(linetokens[i.next()])

        return True

    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None


class MyCSV2(dataseries.OHLCDateTime):
    _linecls = linebuffer.LineBufferFull

    def __init__(self, path):
        self.path = path
        self.f = None

    def getdata(self):
        return self

    def start(self):
        self.reset()

        try:
            self.f = open(self.path, 'rb')
        except IOError:
            self.f = None
            return

        # skip the headers line
        self.f.readline()

        while self.load():
            pass

        self.home()
        self.blen = self.buflen()
        self.curidx = 0

    def preload(self):
        # one time calculation
        pass # done in start

    def next(self):
        if self.curidx < self.blen:
            self.curidx += 1
            self.advance()
            return True
        return False

    def load(self):
        if self.f is None:
            return False

        try:
            line = self.f.readline()
        except (IOError, ValueError,):
            self.f.close()
            self.f = None
            return False

        if not line:
            return False

        linetokens = line.rstrip('\r\n').split(',')

        self.forward() # advance data pointer
        i = itertools.count(0)
        i.next() # skip ticker name
        isday = linetokens[i.next()] == 'D'

        dttxt = linetokens[i.next()]
        y, m, d = int(dttxt[0:4]), int(dttxt[4:6]), int(dttxt[6:8])
        self.lines.date = datetime.date(y, m, d).toordinal()

        tmtxt = linetokens[i.next()]
        if not isday:
            hh, mm, ss = int(tmtxt[0:2]), int(tmtxt[2:4]), int(tmtxt[4:6])
            self.lines.time = hh * 60 * 60 + mm * 60 + ss
        else:
            self.lines.time = 0

        self.lines.open = float(linetokens[i.next()])
        self.lines.high = float(linetokens[i.next()])
        self.lines.low = float(linetokens[i.next()])
        self.lines.close = float(linetokens[i.next()])
        self.lines.volume = float(linetokens[i.next()])
        self.lines.openinterest = float(linetokens[i.next()])

        return True

    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None


MyCSV = MyCSV2
