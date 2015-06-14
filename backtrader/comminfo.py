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


import six

from .metabase import MetaParams


class CommissionInfo(six.with_metaclass(MetaParams)):
    '''CommissionInfo

    This class tries to cover commision schemes for elements which have a cost
    based on price * size (ex: acquiring stocks and later selling them) and
    other things like futures in which the cost of an operation is determined
    by the needed cash margin.

    It also calculates the cash adjustment which is performed on a daily basis
    with futures.

    Params:
      - commission: % of fixed per element commission in monetary units
      - mult: multiplier for futures-like operations
      - margin: amount of cash needed for each futures like contracts

    Note:
      `margin` is the key parameter to decide if a commision is calculate for a
      futures-like object or for a stocks like.

      If margin evaluates to "False" (0, 0.0, None, ...) commissions will be
      calculated for stock like objects.

      Otherwise the calculated commissions and cash adjustments will be done
      for futures-like objects
    '''

    params = (('commission', 0.0), ('mult', 1.0), ('margin', None),)

    def __getattr__(self, name):
        # dig into self.params if not attribute, mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            raise AttributeError

        super(CommInfo, self).__setattribute__(name, value)

    def checkmargin(self, size, price, cash):
        '''Calculates if cash is enough to execute an operation'''
        return cash >= (size * (self.margin or price))

    def getoperationcost(self, size, price):
        '''Returns the needed amount of cash an operation would cost'''
        return size * (self.margin or price)

    def getvalue(self, position, price):
        '''Returns the value of a position given a price. For future-like
        objects it is fixed at size * margin'''
        if self.margin:
            return abs(position.size) * self.margin

        return position.size * price

    def getcomm_pricesize(self, size, price):
        '''Calculates the commission of an operation at a given price
        For future-liek objects the price plays no role'''
        price = price if not self.margin else 1.0
        return size * self.commission * price

    def getcommission(self, order):
        '''Given an order return the actual commission cost'''
        price = order.price if not self.margin else 1.0
        return order.size * self.commission * price

    def profitandloss(self, position, price):
        '''Return actual profit and loss a position has'''
        return position.size * (price - position.price) * self.mult

    def mustcheckmargin(self):
        return not self.margin

    def cashadjust(self, size, price, newprice):
        '''Calculates the adjustment in cash for a given price difference for
        future-like objects'''
        if not self.margin:
            # No margin, no need to adjust -> stock like assume
            return 0.0

        return size * (newprice - price) * self.mult
