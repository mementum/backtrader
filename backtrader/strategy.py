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

import six

from .broker import BrokerBack
from .lineiterator import LineIterator, StrategyBase
from .analyzer import Analyzer
from .sizer import SizerFix
from .datapos import Operation


class MetaStrategy(StrategyBase.__class__):
    def dopreinit(cls, _obj, env, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.env = env
        _obj.broker = env.broker
        _obj._sizer = SizerFix()
        _obj._orders = list()
        _obj._orderspending = list()
        _obj._operations = collections.defaultdict(list)
        _obj._current_ops = dict()
        _obj._operationspending = list()

        if _obj.params._analyzer in [False, None]:
            _obj.analyzer = None
            pass  # requested nothing
        elif _obj.params._analyzer is True:
            # Default to be used
            _obj.analyzer = _obj.stats = Analyzer()
        elif isinstance(_obj.params._analyzer, (list, tuple)):
            # a custom analyzer a tuple/list is expected
            aclass = _obj.params._analyzer[0]

            akwargs = dict()
            if len(_obj.params._analyzer) > 1:
                akwargs = _obj.params._analyzer[1]

            _obj.analyzer = aclass(**akwargs)

        else:
            # assume a class was passed
            _obj.analyzer = _obj.params._analyzer()

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopostinit(_obj, *args, **kwargs)

        dataids = [id(data) for data in _obj.datas]

        _dminperiods = collections.defaultdict(list)
        for lineiter in _obj._lineiterators[LineIterator.IndType]:
            # if multiple datas are used and multiple timeframes the larger
            # timeframe may place larger time constraints in calling next.
            clk = getattr(lineiter, '_clock', None)
            if clk is None:
                clk = getattr(lineiter._owner, '_clock', None)
                if clk is None:
                    continue

            while True:
                if id(clk) in dataids:
                    break

                clk2 = getattr(clk, '._clock', None)
                if clk2 is None:
                    clk2 = getattr(clk._owner, '._clock', None)

                clk = clk2
                if clk is None:
                    break

            if clk is None:
                continue

            _dminperiods[clk].append(lineiter._minperiod)

        _obj._minperiods = list()
        for data in _obj.datas:
            dminperiod = max(_dminperiods[data] or [_obj._minperiod])
            _obj._minperiods.append(dminperiod)

        # Set the minperiod
        minperiods = \
            [x._minperiod for x in _obj._lineiterators[LineIterator.IndType]]
        _obj._minperiod = max(minperiods or [_obj._minperiod])

        if not _obj._sizer.getbroker():
            _obj._sizer.setbroker(_obj.broker)

        # change operators to stage 2
        _obj._stage2()

        return _obj, args, kwargs


class Strategy(six.with_metaclass(MetaStrategy, StrategyBase)):
    _ltype = LineIterator.StratType

    # This unnamed line is meant to allow having "len" and "forwarding"
    extralines = 1

    params = (('_analyzer', True),)

    def _oncepost(self):
        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator.advance()

        self.advance()
        self._notify()

        # check the min period status connected to datas
        dlens = map(operator.sub, self._minperiods, map(len, self.datas))
        minperstatus = max(dlens)

        if minperstatus < 0:
            self.next()
        elif minperstatus == 0:
            self.nextstart()  # only called for the 1st value
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

        self._operationspending = list()

    def _addnotification(self, order):
        self._orderspending.append(order)

        if not order.executed.size:
            return

        opdata = order.data
        dataops = self._operations[opdata]
        if not dataops:
            dataops.append(Operation(data=opdata))

        operation = dataops[-1]

        for exbit in order.executed.exbits:
            operation.update(exbit.closed,
                             exbit.price,
                             exbit.closedvalue,
                             exbit.closedcomm,
                             exbit.pnl)

            if operation.isclosed:
                self._operationspending.append(operation)

                # Open the next operation
                operation = Operation(data=opdata)
                dataops.append(operation)

            # Update it if needed
            operation.update(exbit.opened,
                             exbit.price,
                             exbit.openedvalue,
                             exbit.openedcomm,
                             exbit.pnl)

            if operation.justopened:
                self._operationspending.append(operation)

    def _notify(self):
        for order in self._orderspending:
            self.notify(order)

        for operation in self._operationspending:
            self.notify_operation(operation)

    def notify(self, order):
        pass

    def notify_operation(self, operation):
        pass

    def buy(self, data=None, size=None, price=None, exectype=None, valid=None):
        data = data or self.datas[0]
        size = size or self.getsizing(data)
        return self.broker.buy(
            self, data, size=size, price=price, exectype=exectype, valid=valid)

    def sell(self,
             data=None, size=None, price=None, exectype=None, valid=None):
        data = data or self.datas[0]
        size = size or self.getsizing(data)
        return self.broker.sell(
            self, data, size=size, price=price, exectype=exectype, valid=valid)

    def close(self,
              data=None, size=None, price=None, exectype=None, valid=None):
        possize = self.getposition(data, self.broker).size
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
