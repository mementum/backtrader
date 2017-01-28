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
from backtrader.utils import AutoOrderedDict


class DrawDown(bt.Analyzer):
    '''This analyzer calculates trading system drawdowns stats such as drawdown
    values in %s and in dollars, max drawdown in %s and in dollars, drawdown
    length and drawdown max length

    Params:

      - *None*

    Methods:

      - ``get_analysis``

        Returns a dictionary (with . notation support and subdctionaries) with
        drawdown stats as values, the following keys/attributes are available:

        - ``drawdown`` - drawdown value in 0.xx %
        - ``moneydown`` - drawdown value in monetary units
        - ``len`` - drawdown length

        - ``max.drawdown`` - max drawdown value in 0.xx %
        - ``max.moneydown`` - max drawdown value in monetary units
        - ``max.len`` - max drawdown length
    '''

    def create_analysis(self):
        self.rets = AutoOrderedDict()  # dict with . notation

        self.rets.len = 0
        self.rets.drawdown = 0.0
        self.rets.moneydown = 0.0

        self.rets.max.len = 0.0
        self.rets.max.drawdown = 0.0
        self.rets.max.moneydown = 0.0

        self._maxvalue = float('-inf')  # any value will outdo it

    def stop(self):
        self.rets._close()  # . notation cannot create more keys

    def notify_cashvalue(self, cash, value):
        self._value = value  # record current value
        self._maxvalue = max(self._maxvalue, value)  # update peak value

    def next(self):
        r = self.rets

        # calculate current drawdown values
        r.moneydown = moneydown = self._maxvalue - self._value
        r.drawdown = drawdown = 100.0 * moneydown / self._maxvalue

        # maxximum drawdown values
        r.max.moneydown = max(r.max.moneydown, moneydown)
        r.max.drawdown = maxdrawdown = max(r.max.drawdown, drawdown)

        r.len = r.len + 1 if drawdown else 0
        r.max.len = max(r.max.len, r.len)
