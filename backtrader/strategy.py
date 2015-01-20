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

from lineiterator import LineIterator, Parameter


class MetaStrategy(LineIterator.__metaclass__):

    def dopreinit(cls, _obj, env, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj._clock = env.datas[0]
        _obj._len = 0
        _obj._broker = env.brokers[0] if env.brokers else None
        _obj.env = env
        _obj.datas = env.datas
        return _obj, args[1:], kwargs


class Strategy(LineIterator):
    __metaclass__ = MetaStrategy

    extralines = 1

    def start(self):
        pass

    def stop(self):
        pass

    # Need to simulate len and forwarding because systems have no "lines"
    # This may change in the future
    if True:
        def __len__(self):
            return self._len

        def forward(self):
            self._len += 1

    def setbroker(self, broker):
        self._broker = broker

    def getbroker(self):
        return self._broker

    def _ordernotify(self, order):
        self.ordernotify(order)

    def ordernotify(self, order):
        pass

    def buy(self, data, size, price=None, exectype=None, valid=None):
        return self._broker.buy(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def sell(self, data, size, price=None, exectype=None, valid=None):
        return self._broker.sell(self, data, size=size, price=price, exectype=exectype, valid=valid)

    def position(self, data):
        return self._broker.getposition(data)
