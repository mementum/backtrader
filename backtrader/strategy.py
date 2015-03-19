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

import six

from .broker import BrokerBack
from .lineiterator import LineIterator, StrategyBase
from .analyzer import Analyzer
from .sizer import SizerFix


class MetaStrategy(StrategyBase.__class__):
    def dopreinit(cls, _obj, env, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.env = env
        _obj.broker = env.broker
        _obj._sizer = SizerFix()
        _obj._orders = list()
        _obj._orderspending = list()

        # Create an analyzer
        if _obj.params.analyzer:
            _obj.analyzer = Analyzer()

        # Keep a copy of the created observers by the Analyzer
        _obj._analyzer_obs = _obj._lineiterators[LineIterator.ObsType][:]

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).dopostinit(_obj, *args, **kwargs)

        if not _obj._sizer.getbroker():
            _obj._sizer.setbroker(_obj.broker)

        return _obj, args, kwargs


class Strategy(six.with_metaclass(MetaStrategy, StrategyBase)):
    _ltype = LineIterator.StratType

    # This unnamed line is meant to allow having "len" and "forwarding"
    extralines = 1

    params = (('analyzer', True),)

    def _oncepost(self):
        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator.advance()

        self.advance()
        self._notify()

        l = len(self)
        if l > self._minperiod:
            self.next()
        elif l == self._minperiod:
            self.nextstart() # only called for the 1st value
        else:
            self.prenext()

        for observer in self._lineiterators[LineIterator.ObsType]:
            observer.advance()
            observer.next()

        self.clear()

    def _next(self):
         super(Strategy, self)._next()
         self.clear()

    def start(self):
        pass

    def stop(self):
        pass

    def clear(self):
        self._orders.extend(self._orderspending)
        self._orderspending = list()

    def _addnotification(self, order):
        self._orderspending.append(order)

    def _notify(self):
        for order in self._orderspending:
            self.notify(order)

    def notify(self, order):
        pass

    def buy(self, data=None, size=None, price=None, exectype=None, valid=None):
        data = data or self.datas[0]
        size = size or self.getsizing(data)
        return self.broker.buy(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def sell(self, data=None, size=None, price=None, exectype=None, valid=None):
        data = data or self.datas[0]
        size = size or self.getsizing(data)
        return self.broker.sell(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def close(self, data=None, size=None, price=None, exectype=None, valid=None):
        possize = self.getposition(data, broker).size
        size = abs(size or possize)

        if possize > 0:
            return self.sell(data, size, price, exectype, valid)
        elif possize < 0:
            return self.buy(data, size, price, exectype, valid)

        return None

    def getposition(self, data=None, broker=None):
        data = data or self.datas[0]
        return self.broker.getposition(data)

    position = property(getposition)

    def setsizer(self, sizer):
        self._sizer = sizer
        if not sizer.getbroker():
            sizer.setbroker(self.broker)
        return sizer

    def getsizer(self):
        return self._sizer

    sizer = property(getsizer, setsizer)

    def getsizing(self, data=None):
        data = data or self.datas[0]
        return self._sizer.getsizing(data)

    def delanalyzer(self):
        '''
        This is a one time operation, because is meant to replace the automatically
        generated "analyzer" by (before init) keeping a list of the observers created
        by the analyzer.

        A user-generated analyzer can be kept in a member variable by the user.
        No need to keep it in the system any longer
        '''

        # Remove the observers added by the previous analyzer
        observers = _obj._lineiterators[LineIterator.ObsType]
        for obs in _obj._analyzer_obs:
            observers.remove(obs)

        self.analyzer = None
        _obj._analyzer_obs = list()
