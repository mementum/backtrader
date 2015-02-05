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


class MetaStrategy(LineIterator.__metaclass__):
    def dopreinit(cls, _obj, env, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.env = env
        _obj._broker = env.brokers[0] if env.brokers else (env.addbroker(BrokerBack()) or env.brokers[0])

        return _obj, args, kwargs


class Strategy(LineIterator):
    __metaclass__ = MetaStrategy

    # This unnamed line is meant to allow having "len" and "forwarding"
    # This
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

    def buy(self, data=None, size=1, price=None, exectype=None, valid=None):
        if data is None:
            data = self.datas[0]

        return self._broker.buy(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def sell(self, data=None, size=1, price=None, exectype=None, valid=None):
        if data is None:
            data = self.datas[0]

        return self._broker.sell(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def close(self, data=None, size=None, price=None, exectype=None, valid=None):
        if data is None:
            data = self.datas[0]

        possize = self.getposition(data).size
        if size is None:
            size = possize # no size passed, close entire open position

        size = abs(size) # closing ... not opening anything

        if possize > 0:
            return self.sell(data, abs(size), price, exectype, valid)
        elif possize < 0:
            return self.buy(data, abs(size), price, exectype, valid)
        else:
            # if no position do nothing
            pass

        return None

    def getposition(self, data=None):
        if data is None:
            data = self.datas[0]

        return self._broker.getposition(data)
