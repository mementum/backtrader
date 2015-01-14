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
import abc
import collections

import linebuffer


# Deriving our root metaclass from ABCMeta allows any of the classes below
# to have abstract methods

class MetaRootLine(abc.ABCMeta):
    def doprenew(cls, *args, **kwargs):
        return cls, args, kwargs

    def donew(cls, *args, **kwargs):
        obj = cls.__new__(cls, *args, **kwargs)
        return obj, args, kwargs

    def dopreinit(cls, obj, *args, **kwargs):
        return obj, args, kwargs

    def doinit(cls, obj, *args, **kwargs):
        obj.__init__(*args, **kwargs)
        return obj, args, kwargs

    def dopostinit(cls, obj, *args, **kwargs):
        return obj, args, kwargs

    def __call__(cls, *args, **kwargs):
        cls, args, kwargs = cls.doprenew(*args, **kwargs)
        obj, args, kwargs = cls.donew(*args, **kwargs)
        obj, args, kwargs = cls.dopreinit(obj, *args, **kwargs)
        obj, args, kwargs = cls.doinit(obj, *args, **kwargs)
        obj, args, kwargs = cls.dopostinit(obj, *args, **kwargs)
        return obj


class RootLine(object):
    __metaclass__ = MetaRootLine


class LineAlias(object):
    def __init__(self, line):
        self.line = line

    def __get__(self, obj, cls=None):
        return obj.lines[self.line]

    def __set__(self, obj, value):
        obj.lines[self.line][0] = value


class MetaLines(type):
    linealiases = dict()

    def __new__(meta, name, bases, dct):
        # linealiases = dct.pop('linealiases', list())[:]
        linealiases = dct.get('linealiases', list())[:]

        cls = super(MetaLines, meta).__new__(meta, name, bases, dct)
        for line, linealias in enumerate(linealiases):
            if not isinstance(linealias, basestring):
                linealias = linealias[0] # a tuple or list was passed
            setattr(cls, linealias, LineAlias(line))

        meta.linealiases[cls] = linealiases
        return cls

    def __call__(cls, *args, **kwargs):
        obj = super(MetaLines, cls).__call__(*args, **kwargs)

        # Done to guarantee the lines exist and avoid losing the 1st data value in a line
        # The caller may use additional (non-name declared) lines for internal calculations
        # and the defaultdict ensures the Line will be created automatically
        # The defined ones will always be present.
        # Done in __metaclass__.__call__ to prevent adding a class variable to Lines
        for line, linealias in enumerate(MetaLines.linealiases[cls]):
            # simply asking for the key will force defaultdict to create the value
            obj.lines[line]
            if not isinstance(linealias, basestring):
                # a tuple or list was passed
                aliasname, aliastype = linealias
                if aliastype == 'dt':
                    obj.lines[line] = obj.lines[line].linedate()
                elif aliastype == 'tm':
                    obj.lines[line] = obj.lines[line].linetime()

        return obj


class Lines(object):
    __metaclass__ = MetaLines

    LineCls = linebuffer.LineBufferFull

    def __init__(self):
        self.lines = collections.defaultdict(self.LineCls)

    def __len__(self):
        return len(self.lines[0])

    def size(self):
        return len(self.lines)

    def __getitem__(self, line):
        return self.lines[line]

    def get(self, ago=0, size=1, line=0):
        return self.lines[line].get(ago, size=size)

    def __setitem__(self, line, value):
        self.lines[line][0] = value

    def forward(self, value=linebuffer.NAN):
        for line in self.lines.itervalues():
            line.forward(value)

    def reset(self):
        for line in self.lines.itervalues():
            line.reset()

    def home(self):
        for line in self.lines.itervalues():
            line.home()

    def advance(self):
        for line in self.lines.itervalues():
            line.advance()

    def buflen(self, line=0):
        return self.lines[line].buflen()


class MetaLineSeries(RootLine.__metaclass__):

    def __new__(meta, name, bases, dct):
        lines = dct.pop('lines', list())
        cls = super(MetaLineSeries, meta).__new__(meta, name, bases, dct)
        linecls = getattr(cls, 'linecls', Lines.LineCls)
        baseslines = getattr(cls, 'lines', list())[:]
        baseslines.extend(lines)
        cls.lines = baseslines
        cls._Lines = type(Lines.__name__ + '_'  + name, (Lines,), {'linealiases': cls.lines, 'LineCls': linecls})
        return cls

    def dopreinit(cls, obj, *args, **kwargs):
        obj, args, kwargs = super(MetaLineSeries, cls).dopreinit(obj, *args, **kwargs)
         # obj.lines shadows the class lines (list) definition in the instance
        obj.lines = cls._Lines()
        obj._minperiod = 1
        return obj, args, kwargs


class LineSeries(RootLine):
    __metaclass__ = MetaLineSeries

    def __getattr__(self, name):
        # to refer to line by name directly if the attribute was not found in this object
        # if we set an attribute in this object it will be found before we end up here
        return getattr(self.lines, name)

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, line):
        return self.lines[line]

    def __setitem__(self, line, value):
        self.lines[line][0] = value

    def docalc(self):
        pass
