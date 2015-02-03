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
import collections

import linebuffer
import metabase


class LineAlias(object):
    def __init__(self, line):
        self.line = line

    def __get__(self, obj, cls=None):
        return obj.lines[self.line]

    def __set__(self, obj, value):
        obj.lines[self.line][0] = value


class Lines(object):
    _getlinesbase = classmethod(lambda cls: ())
    _getlines = classmethod(lambda cls: ())
    _getlinesextra = classmethod(lambda cls: 0)
    _getlinesextrabase = classmethod(lambda cls: 0)

    @classmethod
    def _derive(cls, name, lines, extralines):
        baselines = cls._getlines()
        newlines = baselines + lines

        newextralines = cls._getlinesextra() + extralines

        newcls = type(cls.__name__ + '_' + name, (cls,), {})

        setattr(newcls, '_getlinesbase', getattr(newcls, '_getlines'))
        setattr(newcls, '_getlines', classmethod(lambda cls: newlines))

        setattr(newcls, '_getlinesextrabase', getattr(newcls, '_getlinesextra'))
        setattr(newcls, '_getlinesextra', classmethod(lambda cls: newextralines))

        for line, linealias in enumerate(lines, start=len(baselines)):
            if not isinstance(linealias, basestring):
                # a tuple or list was passed, 1st is name
                linealias = linealias[0]
            setattr(cls, linealias, LineAlias(line))

        return newcls

    def __init__(self):
        self.lines = list()
        for line, linealias in enumerate(self._getlines()):
            kwargs = dict()
            if not isinstance(linealias, basestring):
                # a tuple or list was passed, 1st is name, 2nd is type code
                kwargs['typecode'] = linealias[1]

            self.lines.append(linebuffer.LineBuffer(**kwargs))

        # Add the required extralines
        for i in xrange(self._getlinesextra()):
            self.lines.append(linebuffer.LineBuffer())

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

    def extend(self, value=linebuffer.NAN, size=0):
        for line in self.lines:
            line.extend(value, size)

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


class MetaLineSeries(metabase.MetaParams):
    def __new__(meta, name, bases, dct):
        # Remove the line definition (if any) from the class creation
        newlines = dct.pop('lines', ())
        extralines = dct.pop('extralines', 0)

        # Create the class - pulling in any existing "lines"
        cls = super(MetaLineSeries, meta).__new__(meta, name, bases, dct)
        lines = getattr(cls, 'lines', Lines)

        # Create a subclass of the lines class with our name and newlines and put it in the class
        cls.lines = lines._derive(name, newlines, extralines)

        # return the class
        return cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineSeries, cls).dopreinit(_obj, *args, **kwargs)

        # _obj.lines shadows the lines (class) definition in the class
        _obj.lines = cls.lines()

        # Set the minimum period for any LineSeries (sub)class instance (do it at classlevel ?)
        _obj._minperiod = 1

        return _obj, args, kwargs


class LineSeries(object):
    __metaclass__ = MetaLineSeries

    # Use Parameter but install directly as class attribute
    _name = metabase.Parameter(None)

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
