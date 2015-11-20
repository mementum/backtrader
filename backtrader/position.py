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


class Position(object):
    '''
    Keeps and updates the size and price of a position. The object has no
    relationship to any asset. It only keeps size and price.

    Member Attributes:
      - size (int): current size of the position
      - price (float): current price of the position

    The Position instances can be tested using len(position) to see if size
    is not null
    '''

    def __init__(self, size=0, price=0.0):
        self.size = size
        self.price = price

        self.adjbase = None

    def __len__(self):
        return abs(self.size)

    def __bool__(self):
        return self.size != 0

    __nonzero__ = __bool__

    def clone(self):
        return Position(size=self.size, price=self.price)

    def pseudoupdate(self, size, price):
        return Position(self.size, self.price).update(size, price)

    def update(self, size, price):
        '''
        Updates the current position and returns the updated size, price and
        units used to open/close a position

        Args:
            size (int): amount to update the position size
                size < 0: A sell operation has taken place
                size > 0: A buy operation has taken place

            price (float):
                Must always be positive to ensure consistency

        Returns:
            A tuple (non-named) contaning
               size - new position size
                   Simply the sum of the existing size plus the "size" argument
               price - new position price
                   If a position is increased the new average price will be
                   returned
                   If a position is reduced the price of the reamining size
                   does not chance
                   If a position is closed the price is nullified
                   If a position is reversed the price is the price given as
                   argument
               opened - amount of contracts from argument "size" that were used
                   to open/increase a position.
                   A position can be opened from 0 or can be a reversal.
                   If a reversal is performed then opened is less than "size",
                   because part of "size" will have been used to close the
                   existing position
               closed - amount of units from arguments "size" that were used to
                   close/reduce a position

            Both opened and closed carry the same sign as the "size" argument
            because they refer to a part of the "size" argument
        '''

        oldsize = self.size
        self.size += size

        if not self.size:
            # Update closed existing position
            opened, closed = 0, size
            self.price = 0.0
        elif not oldsize:
            # Update opened a position from 0
            opened, closed = size, 0
            self.price = price
        elif oldsize > 0:  # existing "long" position updated

            if size > 0:  # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size > 0:  # reduced position
                opened, closed = 0, size
                # self.price = self.price

            else:  # self.size < 0 # reversed position form plus to minus
                opened, closed = self.size, -oldsize
                self.price = price

        else:  # oldsize < 0 - existing short position updated

            if size < 0:  # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size < 0:  # reduced position
                opened, closed = 0, size
                # self.price = self.price

            else:  # self.size > 0 - reversed position from minus to plus
                opened, closed = self.size, -oldsize
                self.price = price

        return self.size, self.price, opened, closed
