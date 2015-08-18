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

import six

from backtrader import MetaParams, Strategy
import backtrader.metabase as metabase


class MetaAnalyzer(MetaParams):
    def donew(cls, *args, **kwargs):
        '''
        Intercept the strategy parameter
        '''
        # Create the object and set the params in place
        _obj, args, kwargs = super(MetaAnalyzer, cls).donew(*args, **kwargs)

        _obj._children = list()

        _obj.strategy = metabase.findowner(_obj, Strategy)
        _obj._parent = metabase.findowner(_obj, Analyzer)

        # Return to the normal chain
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAnalyzer, cls).dopostinit(_obj, *args, **kwargs)

        if _obj._parent is not None:
            _obj._parent._register(_obj)

        # Return to the normal chain
        return _obj, args, kwargs


class Analyzer(six.with_metaclass(MetaAnalyzer, object)):
    def __len__(self):
        return len(self.strategy)

    def _register(self, child):
        self._children.append(child)

    def _prenext(self):
        for child in self._children:
            child._prenext()

        self.prenext()

    def _nextstart(self):
        for child in self._children:
            child._nextstart()

        self.nextstart()

    def _next(self):
        for child in self._children:
            child._next()

        self.next()

    def _start(self):
        for child in self._children:
            child._start()

        self.start()

    def _stop(self):
        for child in self._children:
            child._stop()

        self.stop()

    def next(self):
        pass

    def prenext(self):
        self.next()

    def nextstart(self):
        self.next()

    def start(self):
        pass

    def stop(self):
        pass
