#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
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
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import operator

from .utils.py3 import map, range, zip, with_metaclass, string_types

from .lineroot import LineRoot
from .lineseries import LineSeries, LineSeriesMaker
from .dataseries import DataSeries
from . import metabase


class MetaLineIterator(LineSeries.__class__):
    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineIterator, cls).donew(*args, **kwargs)

        # Scan args for datas ... if none are found,
        # use the _owner (to have a clock)
        _obj.datas = \
            [LineSeriesMaker(x) for x in args if isinstance(x, LineRoot)]

        # Remove the datas from the args ...
        # already being given to the line iterator
        newargs = [x for x in args if not isinstance(x, LineRoot)]

        # If no datas have been passed to an indicator ... use the
        # main data of the owner, easing up adding "self.data" ...
        if not _obj.datas and isinstance(_obj, (IndicatorBase, ObserverBase)):
            _obj.datas = [_obj._owner.datas[0]]

        # For each found data add access member -
        # for the first data 2 (data and data0)
        if _obj.datas:
            _obj.data = data = _obj.datas[0]

            for l, line in enumerate(data.lines):
                linealias = data._getlinealias(l)
                if linealias:
                    setattr(_obj, 'data_%s' % linealias, line)
                setattr(_obj, 'data_%d' % l, line)

            for d, data in enumerate(_obj.datas):
                setattr(_obj, 'data%d' % d, data)

                for l, line in enumerate(data.lines):
                    linealias = data._getlinealias(l)
                    if linealias:
                        setattr(_obj, 'data%d_%s' % (d, linealias), line)
                    setattr(_obj, 'data%d_%d' % (d, l), line)

        # Parameter values have now been set before __init__
        return _obj, newargs, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineIterator, cls).dopreinit(_obj, *args, **kwargs)

        # if no datas were found use, use the _owner (to have a clock)
        _obj.datas = _obj.datas or [_obj._owner]

        # 1st data source is our ticking clock
        _obj._clock = _obj.datas[0]

        # To automatically set the period Start by scanning the found datas
        # No calculation can take place until all datas have yielded "data"
        # A data could be an indicator and it could take x bars until
        # something is produced
        _obj._minperiod = \
            max([x._minperiod for x in _obj.datas] or [_obj._minperiod])

        # The lines carry at least the same minperiod as
        # that provided by the datas
        for line in _obj.lines:
            line.addminperiod(_obj._minperiod)

        # Prepare to hold children that need to be calculated and
        # influence minperiod
        _obj._lineiterators = collections.defaultdict(list)

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaLineIterator, cls).dopostinit(_obj, *args, **kwargs)

        # my minperiod is as large as the minperiod of my lines
        _obj._minperiod = max([x._minperiod for x in _obj.lines])

        # Recalc the period
        _obj._periodrecalc()

        # Register (my)self as indicator to owner once
        # _minperiod has been calculated
        if _obj._owner is not None:
            _obj._owner.addindicator(_obj)

        return _obj, args, kwargs


class LineIterator(with_metaclass(MetaLineIterator, LineSeries)):
    _ltype = LineSeries.IndType

    plotinfo = dict(plot=True,
                    subplot=True,
                    plotname='',
                    plotskip=False,
                    plotabove=False,
                    plotlinelabels=False,
                    plotymargin=0.0,
                    plotyhlines=[],
                    plotyticks=[],
                    plothlines=[],
                    plotforce=False,
                    plotmaster=None,)

    def _periodrecalc(self):
        # last check in case not all lineiterators were assigned to
        # lines (directly or indirectly after some operations)
        # An example is Kaufman's Adaptive Moving Average
        indicators = self._lineiterators[LineIterator.IndType]
        indperiods = [ind._minperiod for ind in indicators]
        indminperiod = max(indperiods or [self._minperiod])
        self.updateminperiod(indminperiod)

    def _stage2(self):
        super(LineIterator, self)._stage2()

        for data in self.datas:
            data._stage2()

        for lineiterators in self._lineiterators.values():
            for lineiterator in lineiterators:
                lineiterator._stage2()

    def _stage1(self):
        super(LineIterator, self)._stage1()

        for data in self.datas:
            data._stage1()

        for lineiterators in self._lineiterators.values():
            for lineiterator in lineiterators:
                lineiterator._stage1()

    def getindicators(self):
        return self._lineiterators[LineIterator.IndType]

    def getobservers(self):
        return self._lineiterators[LineIterator.ObsType]

    def addindicator(self, indicator):
        # store in right queue
        self._lineiterators[indicator._ltype].append(indicator)

    def bindlines(self, owner=None, own=None):
        if not owner:
            owner = 0

        if isinstance(owner, string_types):
            owner = [owner]
        elif not isinstance(owner, collections.Iterable):
            owner = [owner]

        if not own:
            own = range(len(owner))

        if isinstance(own, string_types):
            own = [own]
        elif not isinstance(own, collections.Iterable):
            own = [own]

        for lineowner, lineown in zip(owner, own):
            if isinstance(lineowner, string_types):
                lownerref = getattr(self._owner.lines, lineowner)
            else:
                lownerref = self._owner.lines[lineowner]

            if isinstance(lineown, string_types):
                lownref = getattr(self.lines, lineown)
            else:
                lownref = self.lines[lineown]

            lownref.addbinding(lownerref)

        return self

    # Alias which may be more readable
    bind2lines = bindlines
    bind2line = bind2lines

    def _next(self):
        clock_len = len(self._clock)
        if clock_len != len(self):
            self.forward()

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator._next()

        self._notify()

        if self._ltype == LineIterator.StratType:
            # supporting datas with different lengths
            dlens = map(operator.sub, self._minperiods, map(len, self.datas))
            minperstatus = max(dlens)
            if minperstatus < 0:
                self.next()
            elif minperstatus == 0:
                self.nextstart()  # only called for the 1st value
            else:
                self.prenext()
        else:
            # assume indicators and others operate on same length datas
            # although the above operation can be generalized
            if clock_len > self._minperiod:
                self.next()
            elif clock_len == self._minperiod:
                self.nextstart()  # only called for the 1st value
            else:
                self.prenext()

    def _once(self):
        self.forward(size=self._clock.buflen())

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator._once()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.forward(size=self.buflen())

        for data in self.datas:
            data.home()

        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator.home()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.home()

        self.home()

        # These 3 remain empty for a strategy and therefore play no role
        # because a strategy will always be executed on a next basis
        # indicators are each called with its min period
        self.preonce(0, self._minperiod - 1)
        self.oncestart(self._minperiod - 1, self._minperiod)
        self.once(self._minperiod, self.buflen())

        for line in self.lines:
            line.oncebinding()

    def preonce(self, start, end):
        pass

    def oncestart(self, start, end):
        self.once(start, end)

    def once(self, start, end):
        pass

    def prenext(self):
        '''
        This method will be called before the minimum period of all
        datas/indicators have been meet for the strategy to start executing
        '''
        pass

    def nextstart(self):
        '''
        This method will be called once, exactly when the minimum period for
        all datas/indicators have been meet. The default behavior is to call
        next
        '''

        # Called once for 1st full calculation - defaults to regular next
        self.next()

    def next(self):
        '''
        This method will be called for all remaining data points when the
        minimum period for all datas/indicators have been meet.
        '''
        pass

    def _addnotification(self, *args, **kwargs):
        pass

    def _notify(self):
        pass

    def _plotinit(self):
        pass


# This 3 subclasses can be used for identification purposes within LineIterator
# or even outside (like in LineObservers)
# for the 3 subbranches without generating circular import references

class DataAccessor(LineIterator):
    PriceClose = DataSeries.Close
    PriceLow = DataSeries.Low
    PriceHigh = DataSeries.High
    PriceOpen = DataSeries.Open
    PriceVolume = DataSeries.Volume
    PriceOpenInteres = DataSeries.OpenInterest
    PriceDateTime = DataSeries.DateTime


class IndicatorBase(DataAccessor):
    pass


class ObserverBase(DataAccessor):
    pass


class StrategyBase(DataAccessor):
    pass
