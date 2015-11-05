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

from .utils.py3 import with_metaclass
from .metabase import MetaParams


class CommInfoBase(with_metaclass(MetaParams)):
    COMM_PERC, COMM_FIXED = range(2)

    params = (
        ('commission', 0.0), ('mult', 1.0), ('margin', None),
        ('commtype', None),
        ('percabs', False),
        # True -> margin must be set, False must no be set, None: no check
        ('stocklike', False),
    )

    def __init__(self):
        super(CommInfoBase, self).__init__()

        self._stocklike = self.p.stocklike
        self._commtype = self.p.commtype

        # The intial block checks for the behavior of the original
        # CommissionInfo in which the commission scheme (perc/fixed) was
        # determined by parameter margin evaluating to False/True
        # If the parameter "commtype" is None, this behavior is emulated
        # else, the parameter values are used

        if self._commtype is None:  # original CommissionInfo behavior applies
            if self.p.margin:
                self._stocklike = False
                self._commtype = self.COMM_FIXED
            else:
                self._stocklike = True
                self._commtype = self.COMM_PERC

        if self._commtype == self.COMM_PERC and not self.p.percabs:
            self.p.commission /= 100.0

    @property
    def margin(self):
        return self.p.margin

    @property
    def stocklike(self):
        return self._stocklike

    def getoperationcost(self, size, price):
        '''Returns the needed amount of cash an operation would cost'''
        if not self._stocklike:
            return abs(size) * self.p.margin

        return abs(size) * price

    def getvalue(self, position, price):
        '''Returns the value of a position given a price. For future-like
        objects it is fixed at size * margin'''
        if not self._stocklike:
            return abs(position.size) * self.p.margin

        return position.size * price

    def _getcommission(self, size, price, pseudoexec):
        '''Calculates the commission of an operation at a given price

        pseudoexec: if True the operation has not yet been executed
        '''
        if self._commtype == self.COMM_PERC:
            return abs(size) * self.p.commission * price

        return abs(size) * self.p.commission

    def getcommission(self, size, price):
        return self._getcommission(size, price, pseudoexec=True)

    def confirmexec(self, size, price):
        return self._getcommission(size, price, pseudoexec=False)

    def profitandloss(self, size, price, newprice):
        '''Return actual profit and loss a position has'''
        return size * (newprice - price) * self.p.mult

    def cashadjust(self, size, price, newprice):
        '''Calculates cash adjustment for a given price difference'''
        if not self._stocklike:
            return size * (newprice - price) * self.p.mult

        return 0.0


class CommissionInfo(CommInfoBase):
    params = (
        ('percabs', True),  # Original CommissionInfo took 0.xx for percentages
    )
