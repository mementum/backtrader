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


from lineseries import LineSeries
import metabase

class MetaLineIterator(LineSeries.__metaclass__):
    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineIterator, cls).dopreinit(_obj, *args, **kwargs)

        # Find the owner and store it
        _obj._owner = metabase.findowner(_obj, LineIterator)

        # Scan args for datas ... if none are found, use the _owner (to have a clock)
        _obj.datas = [x for x in args if isinstance(x, LineSeries)] or [_obj._owner,]

        # 1st data source is our ticking clock
        _obj._clock = _obj.datas[0]

        # To automatically set the period Start by scanning the found datas
        # No calculation can take place until all datas have yielded "data"
        # A data could be an indicator and it could take x bars until something is produced
        _obj._minperiod = max([x._minperiod for x in _obj.datas] or [_obj._minperiod,])

        # Prepare to hold children
        _obj._indicators = list()

        # Remove the datas from the args ... already being given to the line iterator
        args = filter(lambda x: x not in _obj.datas, args)

        return _obj, args, kwargs

    def doinit(cls, _obj, *args, **kwargs):
        def findbases(kls):
            for base in kls.__bases__:
                if issubclass(base, LineSeries):
                    lst = findbases(base)
                    return lst.append(base) or lst

            return []

        bases = findbases(cls)
        # Filter out bases from which the current __init__ was inherited
        bases = filter(lambda x: cls.__init__ != x.__init__, findbases(cls))

        # Call the needed inits along the chain
        for base in bases:
            base.__init__(_obj, *args, **kwargs)

        _obj, args, kwargs = super(MetaLineIterator, cls).doinit(_obj, *args, **kwargs)
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineIterator, cls).dopostinit(_obj, *args, **kwargs)

        # Register (my)self as indicator (lineiterator) to the owner
        # This can't be done any earlier because my own "minperiod" depens on child indicators
        # which have only registered to myself once "init" is over
        if _obj._owner is not None:
            _obj._owner.addindicator(_obj)

        # Avoid duplicates in own _indicators, keeping order
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

    def bindlines(self, owner=None, own=None):
        if not owner:
            owner = 0
        if not isinstance(owner, collections.Iterable):
            owner = [owner,]

        if not own:
            own = xrange(len(owner))
        if not isinstance(own, collections.Iterable):
            own = [own,]

        for lineowner, lineown in zip(owner, own):
            self.lines[lineown].addbinding(self._owner.lines[lineowner])

        return self

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
