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

from lineseries import LineSeries


class ParamsHolder(object):
    params = collections.defaultdict(list)
    extends = (None, None)

    @classmethod
    def get_params(cls):
        return cls.params[cls]

    @classmethod
    def add_param(cls, name, parameter):
        cls.params[cls].append(name)
        setattr(cls, name, parameter)

    def __setattr__(self, name, value):
        if name not in self.params[self.__class__]:
            # if name not in dir(self):
            raise AttributeError
        object.__setattr__(self, name, value)

    @classmethod
    def sort_params(cls):
        cls.params[cls].sort(key=lambda x: getattr(cls, x)._id)


class Parameter(object):
    _id = itertools.count()

    def __init__(self, default):
        self._id = self.__class__._id.next()

        self.default = default
        self.default_type = type(default) if default is not None else None
        default_function = functools.partial(lambda x: x, default)
        self.cache = collections.defaultdict(default_function)
        # self.cache[None] = default
        self.cache[None] = self # To enable access to attributes and __call__

    def __set__(self, obj, value):
        # value = self.default_type(value) if self.default_type is not None else value
        self.cache[obj] = value

    def __get__(self, obj, cls=None):
        return self.cache[obj or None]

    def __call__(self, *args, **kwargs):
        return self.default


class MetaLineIterator(LineSeries.__metaclass__):
    def __new__(meta, name, bases, dct):
        extends = dct.pop('extends', None)
        extcls = extends[0] if extends is not None else None
        extattr = extends[1] if extends is not None else None

        if extcls is not None:
            pbase = getattr(extcls, ParamsHolder.__name__)
        else:
            pbase = ParamsHolder
            # Look in bases for a subclass of ParamsHolder and create a (sub)class
            for base in bases:
                for mname, mvalue in inspect.getmembers(base):
                    if inspect.isclass(mvalue) and issubclass(mvalue, ParamsHolder):
                        pbase = mvalue
                        break
                else:
                    continue # inner loop came to end without break

                break # broke out of inner loop ... pbase has a value

        paramsholder = type(ParamsHolder.__name__ + '_' + name, (pbase,), {})

        # Keep a copy of the extension (if any)
        setattr(paramsholder, 'extends', extends)

        # Keep a copy of the existing parameters - to keep original creation order
        paramsholder.params[paramsholder] = pbase.params[pbase][:]

        # Intercept the params in the new class and remove them from the dict to avoid creation
        for dname, dvalue in dct.items():
            if isinstance(dvalue, Parameter):
                paramsholder.add_param(dname, dct.pop(dname))

        # Ensure the params have the order in which they were defined
        paramsholder.sort_params()

        if extcls is not None:
            # From "extended"
            linealiases = getattr(extcls._Lines, 'linealiases', list())[:]
            # Self defined (addition)
            lines = dct.pop('lines', list())[:]
            linealiases.extend(lines)
            dct['lines'] = linealiases

        # Create the class
        cls = super(MetaLineIterator, meta).__new__(meta, name, bases, dct)
        # Add the ParamsHolder class (or dynamically created subclass)
        setattr(cls, ParamsHolder.__name__, paramsholder)

        return cls

    def dopreinit(cls, obj, *args, **kwargs):
        obj, args, kwargs = super(MetaLineIterator, cls).dopreinit(obj, *args, **kwargs)

        # mark as not being calculated yet and being a full indicator
        obj._calcslave = False
        obj._naked = 0

        # Set autoscanning of subindicators for minperiod
        obj._minperiodautoscan = True

        # Add an instance of ParamsHolder to the instance
        obj.params = params = cls.ParamsHolder()

        # Intercept param values in the instantiation call
        for kname in kwargs.keys():
            if hasattr(params, kname):
                setattr(params, kname, kwargs.pop(kname))

        # scan the args for "datas" (mayb at least for things defining a _minperiod)
        # obj._datas = [inst for inst in args if hasattr(inst, '_minperiod')]
        obj._datas = [x for x in args if isinstance(x, LineSeries)]

        # To automatically set the period Start by scanning the found datas
        # datas_minperiod = max([data._minperiod for data in self._datas]) - 1
        # No calculation can take place until all datas have yielded "data"
        # A data could be an indicator and it could take x bars until something is produced
        obj._minperiod = max([x._minperiod for x in obj._datas] or [1,])

        obj._indicators = list()
        # Filter datas which are indicators and are not yet under the control of any master
        for data in obj._datas:
            if isinstance(data, LineIterator) and not data._calcslave:
                if data._naked > 0:
                    data._naked -= 1
                    continue

                data._calcslave = True
                obj._indicators.append(data)

        # Prepare for linebindings
        obj._linebindings = dict()

        # Create an extension attribute variable if needed
        extends = getattr(params, 'extends', None)
        extcls = extends[0] if extends is not None else None
        extattr = extends[1] if extends is not None else None
        extbindings = extends[2:] if extends is not None else list()

        if extcls is not None and extattr is not None:
            # Go over the class expected params. Fetch the value from the actual params
            # Pass them as kwargs to the creation of the instance
            extparams = getattr(extcls, ParamsHolder.__name__) # let exception be raised if None
            extkwargs = dict()
            for pname in extparams.get_params():
                extkwargs[pname] = getattr(params, pname)

            extobj = extcls(*args, **extkwargs)
            setattr(obj, extattr, extobj)
            obj.addindicator(extobj)

        for extbinding in extbindings:
            lineself, lineext = extbinding
            obj.bind2lines(lineself, extobj, lineext)

        # Parameter values have now been set before __init__
        return obj, args, kwargs

    def dopostinit(cls, obj, *args, **kwargs):
        obj, args, kwargs = super(MetaLineIterator, cls).dopostinit(obj, *args, **kwargs)

        # Scan the instance for (sub)indicators created during initialization
        for name, indicator in inspect.getmembers(obj):
            if isinstance(indicator, LineIterator):
                # Skip things like '_clock' which must not be considered
                if not name.startswith('_') and not indicator._calcslave:
                    indicator._calcslave = True # lambda does not accept an assignment
                    obj._indicators.append(indicator)

        # Scan the line bindings for indicators which may not be calculated by anyone
        if False:
            for indicator in obj._linebindings:
                if not indicator._calcslave:
                    indicator._calcslave = True
                    obj._indicators.append(indicator)

        # remove potential (data) duplicates (example: kept as copy), sort to ensure ordered calculation
        obj._indicators = list(set(obj._indicators))
        obj._indicators.sort(key=lambda x: x._id)

        # if flagged add the minimum period needed by all subindicators to produce values
        if obj._minperiodautoscan:
            # skip obj._clock if present ... its minperiod was already taken into account pre-init
            indminperiod = [x._minperiod for x in obj._indicators if x not in obj._datas] or [1,]
            minperiod = max(indminperiod) - 1
            obj._minperiod += minperiod

        return obj, args, kwargs


class LineIterator(LineSeries):
    __metaclass__ = MetaLineIterator

    def addindicator(self, indicator):
        if not indicator._calcslave:
            if indicator._naked:
                indicator._naked -= 1
            else:
                indicator._calcslave = True
                self._indicators.append(indicator)

    def setminperiod(self, minperiod, autoscan=True):
        # Add the extra requested by the indicator to the auto-calculated from datas
        # Substract 1 which is the minimum period to avoid carrying over an extra 1
        self._minperiod += minperiod - 1

        # Mark if indicators have to be scanned post-init ...
        self._minperiodautoscan = autoscan

    def bind2lines(self, lines, lineit, itlines=None):
        if not isinstance(lines, collections.Iterable):
            lines = [lines,]

        if itlines is None:
            itlines = xrange(len(lines))
        elif not isinstance(itlines, collections.Iterable):
            itlines = [itlines,]

        for i, line in enumerate(lines):
            lineit.lines[itlines[i]].addbinding(self.lines[line])

        if not lineit._calcslave:
            if lineit._naked:
                lineit._naked -= 1
            else:
                lineit._calcslave = True
                self._indicators.append(lineit)

    def bind2lines2(self, lines, lineit, itlines=None, late=False, clean=True):
        if not isinstance(lines, collections.Iterable):
            lines = [lines,]

        if itlines is None:
            itlines = xrange(len(lines))
        elif not isinstance(itlines, collections.Iterable):
            itlines = [itlines,]

        for i, line in enumerate(lines):
            if clean:
                # Remove from sub-calculation if present
                lineit_old = self._linebindings.get(line, None)
                if lineit_old in self._indicators:
                    self._indicators.remove(lineit_old)

            self._linebindings[lineit] = (line, itlines[i])

        # Late binding
        if late:
            # Out of initialization the indicator will not be detected. Add it manually
            self._indicators.append(lineit)
            # Ensure no duplicates and ordered calculation
            self._indicators = list(set(self._indicators))
            self._indicators.sort(key=lambda x: x._id)
            # Tell the indicator to synchronize to its clock ... it was a late binding
            lineit.synchronize()

    def synchronize(self):
        # Clean the lines
        self.reset()
        # Run a catch-up cycle to synchronize with the clock
        for i in xrange(len(self._clock)):
            self._next()

    def _next(self):
        if self._clock in self._indicators:
            self._clock._next()
            indicators = self._indicators[1:]
        else:
            indicators = self._indicators

        clock_len = len(self._clock)
        if clock_len != len(self):
            self.forward()

        for indicator in indicators:
            indicator._next()

            # If the indicator has a binding ... fill the line
            # if indicator in self._linebindings:
                # line, boundline = self._linebindings[indicator]
                # self.lines[line][0] = indicator.lines[boundline][0]

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
        # This is only called for the 1st full calculation
        # The default is to call the function that calculates each value
        self.next()

    def next(self):
        pass
