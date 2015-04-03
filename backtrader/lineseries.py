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

import collections
import operator

import six

from .linebuffer import LineBuffer, LinesOperation, LineDelay, LineAssign, NAN
from .lineroot import LineSingle, LineMultiple
from .metabase import AutoInfoClass
from . import metabase


class LineAlias(object):
    ''' Descriptor class that store a line reference and returns that line from the owner

    Keyword Args:
        line (int): reference to the line that will be returned fro owner's *lines* buffer

    As a convenience the __set__ method of the descriptor is used not set the *line* reference
    because this is a constant along the live of the descriptor instance, but rather to
    set the value of the *line* at the instant '0' (the current one)
    '''

    def __init__(self, line):
        self.line = line

    def __get__(self, obj, cls=None):
        return obj.lines[self.line]

    def __set__(self, obj, value):
        # obj.lines[self.line][0] = value
        LineAssign(obj.lines[self.line], value)


class Lines(object):
    _getlinesbase = classmethod(lambda cls: ())
    _getlines = classmethod(lambda cls: ())
    _getlinesextra = classmethod(lambda cls: 0)
    _getlinesextrabase = classmethod(lambda cls: 0)

    @classmethod
    def _derive(cls, name, lines, extralines, otherbases):

        obaseslines = ()
        obasesextralines = 0

        for otherbase in otherbases:
            obaseslines += otherbase._getlines()
            obasesextralines += otherbase._getlinesextra()

        baselines = cls._getlines() + obaseslines
        baseextralines = cls._getlinesextra() + obasesextralines

        clslines = baselines + lines
        clsextralines = baseextralines + extralines

        lines2add = obaseslines + lines

        # str for Python 2/3 compatibility
        newcls = type(str(cls.__name__ + '_' + name), (cls,), {})

        setattr(newcls, '_getlinesbase', classmethod(lambda cls: baselines))
        setattr(newcls, '_getlines', classmethod(lambda cls: clslines))

        setattr(newcls, '_getlinesextrabase', classmethod(lambda cls: baseextralines))
        setattr(newcls, '_getlinesextra', classmethod(lambda cls: clsextralines))

        for line, linealias in enumerate(lines2add, start=len(cls._getlines())):
            if not isinstance(linealias, six.string_types):
                # a tuple or list was passed, 1st is name
                linealias = linealias[0]
            setattr(cls, linealias, LineAlias(line))

        return newcls

    @classmethod
    def _getlinealias(cls, i):
        lines = cls._getlines()
        if i >= len(lines):
            return ''
        linealias = lines[i]
        if not isinstance(linealias, six.string_types):
            linealias = linealias[0]
        return linealias

    def __init__(self, initlines=None):
        self.lines = list()
        for line, linealias in enumerate(self._getlines()):
            kwargs = dict()
            if not isinstance(linealias, six.string_types): # a tuple and not just a string
                # typecode is additional arg
                kwargs['typecode'] = linealias[1]

            self.lines.append(LineBuffer(**kwargs))

        # Add the required extralines
        for i in range(self._getlinesextra()):
            if not initlines:
                self.lines.append(LineBuffer())
            else:
                self.lines.append(initlines[i])

    def __len__(self):
        return len(self.lines[0])

    def size(self):
        return len(self.lines) - self._getlinesextra()

    def fullsize(self):
        return len(self.lines)

    def extrasize(self):
        return self._getlinesextra()

    def __getitem__(self, line):
        return self.lines[line]

    def get(self, ago=0, size=1, line=0):
        return self.lines[line].get(ago, size=size)

    def __setitem__(self, line, value):
        self.lines[line][0] = value

    def forward(self, value=NAN, size=1):
        for line in self.lines:
            line.forward(value, size=size)

    def rewind(self, size=1):
        for line in self.lines:
            line.rewind(size)

    def extend(self, value=NAN, size=0):
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


class MetaLineSeries(LineMultiple.__class__):
    def __new__(meta, name, bases, dct):
        # Remove the line definition (if any) from the class creation
        newlines = dct.pop('lines', ())
        extralines = dct.pop('extralines', 0)

        # remove the new plotinfo/plotlines definition if any
        newplotinfo = dict(dct.pop('plotinfo', {}))
        newplotlines = dict(dct.pop('plotlines', {}))

        # Create the class - pulling in any existing "lines"
        cls = super(MetaLineSeries, meta).__new__(meta, name, bases, dct)
        lines = getattr(cls, 'lines', Lines)

        # Create a subclass of the lines class with our name and newlines and put it in the class
        morebaseslines = [x.lines for x in bases[1:] if hasattr(x, 'lines')]
        cls.lines = lines._derive(name, newlines, extralines, morebaseslines)

        # Get a copy from base class plotinfo/plotlines (created with the class or set a default)
        plotinfo = getattr(cls, 'plotinfo', AutoInfoClass)
        plotlines = getattr(cls, 'plotlines', AutoInfoClass)

        # Create a plotinfo/plotlines subclass and set it in the class
        morebasesplotinfo = [x.plotinfo for x in bases[1:] if hasattr(x, 'plotinfo')]
        cls.plotinfo = plotinfo._derive(name, newplotinfo, morebasesplotinfo)

        # Before doing plotline newlines have been added and no plotlineinfo is there add a default
        for line in newlines:
            if not isinstance(line, six.string_types):
                line = line[0]
            newplotlines.setdefault(line, dict())

        morebasesplotlines = [x.plotlines for x in bases[1:] if hasattr(x, 'plotlines')]
        cls.plotlines = plotlines._derive(name, newplotlines, morebasesplotlines, recurse=True)

        # return the class
        return cls

    def donew(cls, *args, **kwargs):
        # _obj.plotinfo shadows the plotinfo (class) definition in the class
        plotinfo = cls.plotinfo()

        for pname, pdef in cls.plotinfo._getitems():
            setattr(plotinfo, pname, kwargs.pop(pname, pdef))

        # Create the object and set the params in place
        _obj, args, kwargs = super(MetaLineSeries, cls).donew(*args, **kwargs)

        # set the plotinfo member in the class
        _obj.plotinfo = plotinfo

        # _obj.lines shadows the lines (class) definition in the class
        _obj.lines = cls.lines()
        if _obj.lines.fullsize():
            _obj.array = _obj.lines[0].array

        # _obj.plotinfo shadows the plotinfo (class) definition in the class
        _obj.plotlines = cls.plotlines()

        # add aliases for lines
        if _obj.lines.fullsize():
            setattr(_obj, 'line', _obj.lines[0])

        for l, line in enumerate(_obj.lines):
            setattr(_obj, 'line_%d' % l, line)
            setattr(_obj, 'line%d' % l, line)

        # Parameter values have now been set before __init__
        return _obj, args, kwargs


class LineSeries(six.with_metaclass(MetaLineSeries, LineMultiple)):
    _name = ''

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

    def __init__(self, *args, **kwargs):
        # if any args, kwargs make it up to here, something is broken
        # defining a __init__ guarantees the existence of im_func to findbases
        # in lineiterator later, because object.__init__ has no im_func (object has slots)
        pass

    def plotlabel(self):
        label = self.plotinfo.plotname or self.__class__.__name__
        sublabels = self._plotlabel()
        if sublabels:
            for i, sublabel in enumerate(sublabels):
                # if isinstance(sublabel, LineSeries): ## DOESN'T WORK ???
                if hasattr(sublabel, 'plotinfo'):
                    sublabels[i] = sublabel.plotinfo.plotname or sublabel.__class__.__name__
            label += ' (%s)' % ', '.join(map(str, sublabels))
        return label

    def _plotlabel(self):
        return self.params._getvalues()

    def __call__(self, ago, line=0):
        return LineDelay(self.lines[line], ago, _ownerskip=self)

    def _operation(self, other, operation, r=False):
        if isinstance(other, LineMultiple):
            # FIXME: ideally return a LineSeries object at least as long as the
            # smallest size of both operands
            return LinesOperation(self.lines[0], other[0], operation, r, _ownerskip=self)
        elif isinstance(other, LineSingle):
            return LinesOperation(self.lines[0], other, operation, r, _ownerskip=self)

        # assume other is a standard type
        return LinesOperation(self.lines[0], other, operation, r, _ownerskip=self)

    def __lt__(self, other):
        return self[0][0] < other

    def __gt__(self, other):
        return self[0][0] > other

    def __le__(self, other):
        return self[0][0] <= other

    def __ge__(self, other):
        return self[0][0] >= other

    def __eq__(self, other):
        if isinstance(other, LineSeries):
            return other is LineSeries
        return self[0][0] == other

    def __ne__(self, other):
        if isinstance(other, LineSeries):
            return other is not LineSeries
        return self[0][0] != other


class LineSeriesStub(LineSeries):
    extralines = 1

    def __init__(self, line):
        self.lines = self.__class__.lines(initlines=[line,])
        # give a change to find the line owner (for plotting at least)
        self.owner = line._owner
        self._minperiod = line._minperiod


def LineSeriesMaker(arg):
    if isinstance(arg, LineSeries):
        return arg

    return LineSeriesStub(arg)
