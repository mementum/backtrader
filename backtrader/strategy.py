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

from lineiterator import LineIterator
from broker import BrokerBack
from positionsizer import PosSizerFix


class MetaStrategy(LineIterator.__metaclass__):
    def dopreinit(cls, _obj, env, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.env = env
        _obj._broker = env.brokers[0] if env.brokers else (env.addbroker(BrokerBack()) or env.brokers[0])
        _obj._possizer = None

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).dopostinit(_obj, *args, **kwargs)

        if not _obj._possizer:
            _obj._possizer = PosSizerFix(broker=_obj._broker)
        elif not _obj._possizer.getbroker():
            _obj._possizer.setbroker(_obj._broker)

        return _obj, args, kwargs


class Strategy(LineIterator):
    __metaclass__ = MetaStrategy

    # This unnamed line is meant to allow having "len" and "forwarding"
    extralines = 1

    def start(self):
        pass

    def stop(self):
        pass

    def setbroker(self, broker):
        self._broker = broker

    def getbroker(self):
        return self._broker

    def _ordernotify(self, order):
        self.ordernotify(order)

    def ordernotify(self, order):
        pass

    def getdatabroker(self, data, broker):
        return data or self.datas[0], broker or self.getbroker()

    def buy(self, data=None, size=None, price=None, exectype=None, valid=None, broker=None):
        data, broker = self.getdatabroker(data, broker)
        size = size or self.getsizing(data, broker)

        return broker.buy(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def sell(self, data=None, size=None, price=None, exectype=None, valid=None, broker=None):
        data, broker = self.getdatabroker(data, broker)
        size = size or self.getsizing(data, broker)

        return broker.sell(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def close(self, data=None, size=None, price=None, exectype=None, valid=None, broker=None):
        possize = self.getposition(data, broker).size
        size = abs(size or possize)

        if possize > 0:
            return self.sell(data, abs(size), price, exectype, valid, broker)
        elif possize < 0:
            return self.buy(data, abs(size), price, exectype, valid, broker)

        return None

    def getposition(self, data=None, broker=None):
        data, broker = self.getdatabroker(data, broker)
        return broker.getposition(data)

    def setpositionsizer(self, possizer):
        self._possizer = possizer

    def getpositionsizer(self):
        return self._possizer

    def getsizing(self, data=None, broker=None):
        data, broker = self.getdatabroker(data, broker)
        return self.getpositionsizer().getsizing(data, broker)
