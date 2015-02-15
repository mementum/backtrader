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
import metabase


class CommissionInfo(object):
    __metaclass__ = metabase.MetaParams

    params = (('commission', 0.0), ('mult', 1.0), ('margin', None),)

    def __getattr__(self, name):
        # dig into self.params if not found as attribute, mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            raise AttributeError

        super(CommInfo, self).__setattribute__(name, value)

    def checkmargin(self, size, price, cash):
        return cash >= (size * (self.margin or price))

    def getoperationcost(self, size, price):
        return size * (self.margin or price)

    def getvalue(self, position, price):
        if self.margin:
            return abs(position.size) * self.margin

        return position.size * price

    def getcomm_pricesize(self, size, price):
        price = price if not self.margin else 1.0
        return size * self.commission * price

    def getcommission(self, order):
        price = order.price if not self.margin else 1.0
        return order.size * self.commission * price

    def profitandloss(self, position, price):
        return position.size * (price - position.price) * self.mult

    def mustcheckmargin(self):
        return not self.margin

    def cashadjust(self, size, price, newprice):
        if not self.margin:
            # No margin, no need to adjust -> stock like assume
            return 0.0

        return size * (newprice - price) * self.mult
