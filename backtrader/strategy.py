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
        _obj.env = env
        _obj._clock = env.datas[0]
        _obj._len = 0
        return _obj, args[1:], kwargs


class Strategy(LineIterator):
    __metaclass__ = MetaStrategy

    def start(self):
        pass

    def stop(self):
        pass

    # Need to simulate len and forwarding because systems have no "lines"
    # This may change in the future
    def __len__(self):
        return self._len

    def forward(self):
        self._len += 1
