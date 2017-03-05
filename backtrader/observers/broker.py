#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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

from .. import Observer


class Cash(Observer):
    '''This observer keeps track of the current amount of cash in the broker

    Params: None
    '''
    _stclock = True

    lines = ('cash',)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines[0][0] = self._owner.broker.getcash()


class Value(Observer):
    '''This observer keeps track of the current portfolio value in the broker
    including the cash

    Params: None
    '''
    _stclock = True

    lines = ('value',)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines[0][0] = self._owner.broker.getvalue()


class Broker(Observer):
    '''This observer keeps track of the current cash amount and portfolio value in
    the broker (including the cash)

    Params: None
    '''
    _stclock = True

    alias = ('CashValue',)
    lines = ('cash', 'value')

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines.cash[0] = self._owner.broker.getcash()
        self.lines.value[0] = value = self._owner.broker.getvalue()
