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

import backtrader as bt


class GrossLeverage(bt.Analyzer):
    '''This analyzer calculates the Gross Leverage of the current strategy
    on a timeframe basis

    Params: None

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    def notify_cashvalue(self, cash, value):
        self._cash = cash
        self._value = value

    def next(self):
        # Updates the leverage for "dtkey" (see base class) for each cycle
        # 0.0 if 100% in cash, 1.0 if no short selling and fully invested
        lev = (self._value - self._cash) / self._value
        self.rets[self.data0.datetime.datetime()] = lev
