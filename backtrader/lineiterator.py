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
import functools
import inspect
import itertools
import sys

from lineseries import LineSeries
from parameters import Params


class MetaLineIterator(LineSeries.__metaclass__):
    def __new__(meta, name, bases, dct):
        # Remove params from class definition to avod inheritance (and hence "repetition")
        newparams = dct.pop('params', ())

        # Create the new class - this pulls predefined "params"
        cls = super(MetaLineIterator, meta).__new__(meta, name, bases, dct)

        # Pulls the param class out of it
        params = getattr(cls, 'params', Params)

        # Look for an extension and if found, add the params
        extend = dct.get('extend', None)
        if extend is not None:
            extcls = extend[0]
            extparams = getattr(extcls, 'params')
            newparams = extparams._getparams() + newparams

        # Subclass and store the existing params with the (extended if any) newly defined params
        cls.params = params._derive(name, newparams)

        # The "extparams" end up in the middle (baseparams + extparams + newparams) which makes sense
        return cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineIterator, cls).dopreinit(_obj, *args, **kwargs)

        # Find the owner and store it
        _obj._owner = None
        for framelevel in itertools.count(1):
            try:
                frame = sys._getframe(framelevel)
            except ValueError:
                # Frame depth exceeded ... no owner ... break away
                break

            # 'self' in regular code ... and '_obj' in metaclasses
            self_ = frame.f_locals.get('self', None)
            obj_ = frame.f_locals.get('_obj', None)
            if self_ != _obj and isinstance(self_, LineIterator):
                _obj._owner = self_
                break
            elif obj_ != _obj and isinstance(obj_, LineIterator):
                _obj._owner = obj_
                break

        # Create params and set the values from the kwargs
        _obj.params = cls.params()
        for kname in kwargs.keys():
            if hasattr(_obj.params, kname):
                setattr(_obj.params, kname, kwargs.pop(kname))

        # scan the args for "datas" (maybe at least for things defining a _minperiod)
        # _obj._datas = [inst for inst in args if hasattr(inst, '_minperiod')]
        _obj._datas = [x for x in args if isinstance(x, LineSeries)]

        # To automatically set the period Start by scanning the found datas
        # datas_minperiod = max([data._minperiod for data in self._datas]) - 1
        # No calculation can take place until all datas have yielded "data"
        # A data could be an indicator and it could take x bars until something is produced
        _obj._minperiod = max([x._minperiod for x in _obj._datas] or [_obj._minperiod,])

        _obj._indicators = list()

        # Create an extension attribute variable if needed
        extend = getattr(_obj, 'extend', None)
        if extend is not None:
            extcls = extend[0]
            # Go over the class expected params. Fetch the value from the actual existing params
            # Pass them as kwargs to the creation of the extended instance
            extparams = getattr(extcls, 'params')
            extkwargs = dict()
            for pname, pdefault in extparams._getparams():
                extkwargs[pname] = getattr(_obj.params, pname)

            extobj = extcls(*args, **extkwargs)
            setattr(_obj, 'extend', extobj)

            # Make sure extended binding to lines have the right offset - start after a potential baseclass
            extoffset = len(cls.lines._getlinesbase())
            for lineself, lineext in extend[1:]:
                _obj.bind2lines(lineself + extoffset, extobj, lineext)

        # Parameter values have now been set before __init__
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineIterator, cls).dopostinit(_obj, *args, **kwargs)

        # Register (my)self as indicator (lineiterator) to the owner
        if _obj._owner is not None:
            _obj._owner.addindicator(_obj)

        # Avoid duplicates in own _indicators
        seen = set()
        _obj._indicators = [x for x in _obj._indicators if x not in seen and not seen.add(x)]

        _obj._clockindicator = False
        if _obj._clock in _obj._indicators:
            # If the clock has not moved forward we won't move our own clock forward
            # Therefore this "clockindidator" has to be calculated first before our clock moves
            # by also taking the "clock" out of the indicator slicing the _indicators member
            # variable must not be done each and every time
            _obj._clockindicator = True
            _obj._indicators = self._indicators[1:] # clock is always first, leave it aside

        return _obj, args, kwargs


class LineIterator(LineSeries):
    __metaclass__ = MetaLineIterator

    def addindicator(self, indicator):
        self._indicators.append(indicator)
        self._minperiod = max(indicator._minperiod, self._minperiod)

    def setminperiod(self, minperiod):
        # Add the extra requested by the indicator to the auto-calculated from datas
        # Substract 1 which is the minimum period to avoid carrying over an extra 1
        self._minperiod += minperiod - 1

    def bind2lines(self, lines, lineit, itlines=None):
        if not isinstance(lines, collections.Iterable):
            lines = [lines,]

        if itlines is None:
            itlines = xrange(len(lines))
        elif not isinstance(itlines, collections.Iterable):
            itlines = [itlines,]

        for i, line in enumerate(lines):
            lineit.lines[itlines[i]].addbinding(self.lines[line])

    def _next(self):
        if self._clockindicator:
            self._clock._next()

        clock_len = len(self._clock)
        if clock_len != len(self):
            self.forward()

        for indicator in self._indicators:
            indicator._next()

        if clock_len > self._minperiod:
            self.next()
        elif clock_len == self._minperiod:
            self.nextstart() # only called for the 1st value
        else:
            # FIXME: Add a differentiation between preperiod and prenext
            self.prenext()

    def _once(self):
        for indicator in self._indicators:
            indicator._once()

        self.once()

    def once(self):
        pass

    def preperiod(self):
        pass

    def prenext(self):
        pass

    def nextstart(self):
        # Called once for 1st full calculation - defaults to regular next
        self.next()

    def next(self):
        pass
