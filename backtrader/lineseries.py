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


# Subclassing from ABCMeta allows later the entire hierarchy to have abstract methods

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


class Lines(object):
    _linecls = linebuffer.LineBufferFull

    _getlinesbase = classmethod(lambda cls: ())
    _getlines = classmethod(lambda cls: ())

    @classmethod
    def _derive(cls, name, lines, linecls):
        baselines = cls._getlines()
        newlines = baselines + lines
        newcls = type(cls.__name__ + '_' + name, (cls,), {})

        setattr(newcls, '_getlinesbase', getattr(newcls, '_getlines'))
        setattr(newcls, '_getlines', classmethod(lambda cls: newlines))

        setattr(newcls, '_linecls', linecls)

        for line, linealias in enumerate(lines, start=len(baselines)):
            if not isinstance(linealias, basestring):
                # a tuple or list was passed, 1st is name
                linealias = linealias[0]
            setattr(cls, linealias, LineAlias(line))

        return newcls

    def __init__(self):
        self.lines = list()
        for line, linealias in enumerate(self._getlines()):
            self.lines.append(self._linecls())
            if not isinstance(linealias, basestring):
                # a tuple or list was passed, 1st is name, 2nd is type code
                aliasname, aliastype = linealias
                if aliastype == 'dt':
                    self.lines[-1] = self.lines[-1].linedate()
                elif aliastype == 'tm':
                    self.lines[-1] = self.lines[-1].linetime()

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
        for line in self.lines:
            line.forward(value)

    def reset(self):
        for line in self.lines:
            line.reset()

    def home(self):
        for line in self.lines:
            line.home()

    def advance(self):
        for line in self.lines:
            line.advance()

    def buflen(self, line=0):
        return self.lines[line].buflen()


class MetaLineSeries(RootLine.__metaclass__):
    def __new__(meta, name, bases, dct):
        # Remove the line definition (if any) from the class creation
        newlines = dct.pop('lines', ())

        # Create the class - pulling in any existing "lines"
        cls = super(MetaLineSeries, meta).__new__(meta, name, bases, dct)
        lines = getattr(cls, 'lines', Lines)

        # Get the linebufferclass to apply
        linebuffercls = getattr(cls, '_linecls', lines._linecls)

        # Look for an extension
        extend = dct.get('extend', None)
        if extend:
            extcls = extend[0]
            extendlines = getattr(extcls, 'lines')
            # lines end up in following order: baselines + extlines + newlines
            newlines = extendlines._getlines() + newlines

        # Create a subclass of the lines class with our name and newlines and put it in the class
        cls.lines = lines._derive(name, newlines, linebuffercls)

        # return the class
        return cls

    def dopreinit(cls, obj, *args, **kwargs):
        obj, args, kwargs = super(MetaLineSeries, cls).dopreinit(obj, *args, **kwargs)

        # obj.lines shadows the lines (class) definition in the class
        obj.lines = cls.lines()

        # Set the minimum period for any LineSeries (sub)class instance
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
