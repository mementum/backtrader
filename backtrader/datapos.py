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
from __future__ import absolute_import, division, print_function, unicode_literals


class Position(object):
    '''
    Keeps and updates the size and price of a position. The object has no relationship
    to any asset. It only keeps size and price.

    Attributes:
        size (int): current size of the position
        price (float): current price of the position

    The Position instances can be tested using len(position) to see if size is not null
    '''

    def __init__(self, size=0, price=0.0):
        self.size = size
        self.price = price

    def __len__(self):
        return self.size

    def update(self, size, price):
        '''
        Updates the current position and returns the updated size, price and units
        used to open/

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
                   If a position is increased the new average price will be returned
                   If a position is reduced the price of the reamining size does not chance
                   If a position is closed the price is nullified
                   If a position is reversed the price is the price given as argument
               opened - amount of contracts from argument "size" that were
                   used to open/increase a position. A position can be opened
                   from 0 or can be a reversal. If a reversal is performed
                   then opened is less than "size", because part os "size" will
                   have been used to close the existing position
               closed - amount of units from arguments "size" that were
                   used to close/reduce a position

            Both opened and closed carry the same sign as the "size" argument because
            they refer to a part of the "size" argument
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
        elif oldsize > 0: # existing "long" position updated

            if size > 0: # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size > 0: # reduced position
                opened, closed = 0, -size
                # self.price = self.price

            else: # self.size < 0 # reversed position form plus to minus
                opened, closed = self.size, -oldsize
                self.price = price

        else: # oldsize < 0 - existing short position updated

            if size < 0: # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size < 0: # reduced position
                opened, closed = 0, -size
                # self.price = self.price

            else: # self.size > 0 - reversed position from minus to plus
                opened, closed = self.size, -oldsize
                self.price = price

        return self.size, self.price, opened, closed


class Operation(object):
    '''
    Keeps track of the life of an operation: size, price, commission (and value?)

    An operation starts at 0 can be increased and reduced and can be considered closed
    if it goes back to 0.

    The operation can be long (positive size) or short (negative size)

    An operation is not meant to be reversed (no support in the logic for it)

    Attributes:
        size (int): current size of the operation
        price (float): current price of the operation
        value (float): current value of the operation
        commission (float): current accumulated commission
        pnl (float): current profit and loss of the operation (gross pnl)
        pnlcomm (float): current profit and loss of the operation minus commission (net pnl)
        isclosed (bool): records if the last update closed (set size to null) the operation
        isopen (bool): records if any update has opened the operation
    '''
    def __init__(self, size=0, price=0.0, value=0.0, commission=0.0):
        self.size = size
        self.price = price
        self.value = value
        self.commission = commission

        self.pnl = 0.0
        self.pnlcomm = 0.0

        self.isopen = False
        self.isclosed = False

    def __len__(self):
        return self.size

    isclosed = __len__

    def update(self, size, price, value, commission):
        '''
        Updates the current operation. The logic does not check if the operation is reversed, which
        is not conceptually supported by the object.

        If an update sets the size attribute to null, "closed" will be set to true

        Args:
            size (int): amount to update the order
                if size has the same sign as the current operation a position increase will happen
                if size has the opposite sign as current op size a reduction/close will happen

            price (float): always be positive to ensure consistency
            value (float): cost incurred in new size/price op
            commission (float): incurred commission in the new size/price op
        '''
        if not size:
            return # empty update, skip all other calculations

        # Commission can only increase
        self.commission += commission

        # Update size and keep a reference for logic an calculations
        oldsize = self.size
        self.size += size # size will carry the opposite sign if reducing

        # Any size means the operation was opened
        self.isopen = True

        # record if the position was closed (set to null)
        self.isclosed = not self.size

        if abs(self.size) > abs(oldsize):
            # position increased (be it positive or negative)
            # update the average price
            self.price = (oldsize * self.price + size * price) / self.size

        else: # abs(self.size) < abs(oldsize)
            # position reduced/closed

            # This is an "update" and therefore the usual formula "current price - original price"
            # to calculate the profit and loss has to be inverted. If the original position is 10
            # reducing/closing the position needs a negative size. If the formula is not inverted
            # profit and loss figures would be inverted
            self.pnl += size * (self.price - price)
            self.pnlcomm = self.pnl - self.commission

        self.value = self.size * self.price
