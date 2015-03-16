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

import six

from .lineseries import LineSeries
from . import metabase

class MetaLineIterator(LineSeries.__class__):
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
        _obj._minperiod = max([data._minperiod for data in _obj.datas] or [_obj._minperiod,])

        # Prepare to hold children that need to be calculated and influence minperiod
        _obj._lineiterators = collections.defaultdict(list)

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

        if getattr(cls, '_autoinit', False):
            # Find and call baseclasses __init__ (from top to bottom)
            seen = set()
            try:
                ownimfunc = _obj.__init__.im_func.__call__ # Python 2 with unbound methods
            except AttributeError:
                ownimfunc = _obj.__init__.__call__ # Python 3 - function object
            for x in findbases(cls):
                try:
                    ximfunc = x.__init__.im_func.__call__ # Python 2 with unbound methods
                except AttributeError:
                    ximfunc = x.__init__.__call__ # Python 3 - function object

                if ximfunc not in seen:
                    seen.add(ximfunc)
                    # only execute the call if it's not our own init, which may have been inherited.
                    if ximfunc != ownimfunc:
                        x.__init__(_obj, *args, **kwargs)

        _obj, args, kwargs = super(MetaLineIterator, cls).doinit(_obj, *args, **kwargs)
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaLineIterator, cls).dopostinit(_obj, *args, **kwargs)

        # Register (my)self as indicator (lineiterator) to the owner
        # This can't be done any earlier because my own "minperiod" depens on child indicators
        # which have only registered to myself once "init" is over
        if _obj._owner is not None:
            _obj._owner.addindicator(_obj)

        # check if the object clock is an indicator (to avoid duplicate calculation)
        _obj._clockindicator = False

        for ltype, liters in _obj._lineiterators.items():
            if _obj._clock in liters:
                # If the clock has not moved forward we won't move our own clock forward
                # Therefore this "clockindidator" has to be calculated first before our clock moves
                # by also taking the "clock" out of the indicator slicing the _lineterators[ltype]
                # member variable must not be done each and every time
                _obj._clockindicator = True
                _obj._lineiterators[ltype] = liters[1:] # clock is always first, leave it aside
                break

        return _obj, args, kwargs


class LineIterator(six.with_metaclass(MetaLineIterator, LineSeries)):
    IndType, StratType, ObsType = list(range(3))

    _ltype = IndType

    plotinfo = dict(plot=True, subplot=True, plotname='', plotskip=False)

    def getindicators(self):
        return self._lineiterators[LineIterator.IndType]

    def getobservers(self):
        return self._lineiterators[LineIterator.ObsType]

    def addindicator(self, indicator):
        # store in right queue
        self._lineiterators[indicator._ltype].append(indicator)
        # if needed used its minperiod
        if indicator._ltype in [LineIterator.IndType, LineIterator.StratType,]:
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
            own = range(len(owner))
        if not isinstance(own, collections.Iterable):
            own = [own,]

        for lineowner, lineown in zip(owner, own):
            self.lines[lineown].addbinding(self._owner.lines[lineowner])

        return self

    def bind2lines(self, lines, lineit, itlines=None):
        if not isinstance(lines, collections.Iterable):
            lines = [lines,]

        if itlines is None:
            itlines = range(len(lines))
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

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator._next()

        self._notify()

        if clock_len > self._minperiod:
            self.next()
        elif clock_len == self._minperiod:
            self.nextstart() # only called for the 1st value
        else:
            # POTENTIAL IDEA: Add an extra method before "prenext" is reached (preminperiod)
            self.prenext()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer._next()

    def _once(self):
        self.forward(size=self._clock.buflen())

        if self._clockindicator:
            self._clock._once()

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator._once()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.forward(size=self.buflen())

        for data in self.datas:
            data.home()

        if self._clockindicator:
            self._clock.home()

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator.home()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.home()

        self.home()

        self.preonce(0, self._minperiod - 1)
        self.once(self._minperiod - 1, self.buflen())

        for line in self.lines:
            line.oncebinding()

    def preonce(self, start, end):
        pass

    def once(self, start, end):
        pass

    def prenext(self):
        pass

    def nextstart(self):
        # Called once for 1st full calculation - defaults to regular next
        self.next()

    def next(self):
        pass

    def _addnotification(self, *args, **kwargs):
        pass

    def _notify(self):
        pass

    def plotlabel(self):
        label = self.plotinfo.plotname or self.__class__.__name__
        sublabel = self._plotlabel()
        if sublabel:
            label += ' (%s)' % sublabel
        return label

    def _plotlabel(self):
        return ','.join(map(str, self.params._getvalues()))
