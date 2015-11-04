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
    COMM_PERC, COMM_FIX = range(2)

    params = (
        ('commission', 0.0), ('mult', 1.0), ('margin', None),
        ('commtype', None),
        ('percfix', True),
        # True -> margin must be set, False must no be set, None: no check
        ('margincheck', None),
    )

    def __init__(self):
        super(CommInfoBase, self).__init__()

        self._commtype = self.p.commtype
        if self._commtype is None:  # original CommissionInfo
            self._commtype = self.COMM_FIX if self.p.margin else self.COMM_PERC

        elif self.p.margincheck is True:  # other object with commtype not None
            if not self.p.margin:
                raise ValueError('%s: margin MUST BE set but it is %s' %
                                 (self.__class__.__name__, str(self.p.margin)))

        elif self.p.margincheck is False:
            if self.p.margin:
                raise ValueError('%s: margin MUST NOT BE set but it is %s' %
                                 (self.__class__.__name__, str(self.p.margin)))

    @property
    def margin(self):
        return self.p.margin

    def stocklike(self):
        return not self.p.margin

    def getoperationcost(self, size, price):
        '''Returns the needed amount of cash an operation would cost'''
        return abs(size) * (self.p.margin or price)

    def getvalue(self, position, price):
        '''Returns the value of a position given a price. For future-like
        objects it is fixed at size * margin'''
        if self.p.margin:
            return abs(position.size) * self.p.margin

        return position.size * price

    def getcomm_pricesize(self, size, price):
        '''Calculates the commission of an operation at a given price'''
        if self._commtype == self.COMM_PERC:
            return abs(size) * self.p.commission * price

        return abs(size) * self.p.commission

    def getcommission(self, order):
        '''Given an order return the actual commission cost'''
        return self.getcomm_pricesize(order.size, order.price)

    def profitandloss(self, size, price, newprice):
        '''Return actual profit and loss a position has'''
        return size * (newprice - price) * self.p.mult

    def cashadjust(self, size, price, newprice):
        '''Calculates cash adjustment for a given price difference'''
        if not self.p.margin:
            # No margin, no need to adjust -> stock like assume
            return 0.0

        return size * (newprice - price) * self.p.mult


class CommissionInfo(CommInfoBase):
    params = (
        ('percfix', False),  # Original object takes 0.xx for percentages
    )
