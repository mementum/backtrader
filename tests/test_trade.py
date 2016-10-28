#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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

import testcommon

import backtrader as bt
from backtrader import trade


class FakeCommInfo(object):
    def getvaluesize(self, size, price):
        return 0

    def profitandloss(self, size, price, newprice):
        return 0


class FakeData(object):
    '''
    Minimal interface to avoid errors when trade tries to get information from
    the data during the test
    '''
    def __len__(self):
        return 0

    @property
    def datetime(self):
        return [0.0]

    @property
    def close(self):
        return [0.0]


def test_run(main=False):
    tr = trade.Trade(data=FakeData())

    order = bt.BuyOrder(data=FakeData(),
                        size=0, price=1.0,
                        exectype=bt.Order.Market,
                        simulated=True)

    commrate = 0.025
    size = 10
    price = 10.0
    value = size * price
    commission = value * commrate

    tr.update(order=order, size=size, price=price, value=value,
              commission=commission, pnl=0.0, comminfo=FakeCommInfo())

    assert not tr.isclosed
    assert tr.size == size
    assert tr.price == price
    # assert tr.value == value
    assert tr.commission == commission
    assert not tr.pnl
    assert not tr.pnlcomm

    upsize = -5
    upprice = 12.5
    upvalue = upsize * upprice
    upcomm = abs(value) * commrate

    tr.update(order=order, size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0, comminfo=FakeCommInfo())

    assert not tr.isclosed
    assert tr.size == size + upsize
    assert tr.price == price  # size is being reduced, price must not change
    # assert tr.value == upvalue
    assert tr.commission == commission + upcomm

    size = tr.size
    price = tr.price
    commission = tr.commission

    upsize = 7
    upprice = 14.5
    upvalue = upsize * upprice
    upcomm = abs(value) * commrate

    tr.update(order=order, size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0, comminfo=FakeCommInfo())

    assert not tr.isclosed
    assert tr.size == size + upsize
    assert tr.price == ((size * price) + (upsize * upprice)) / (size + upsize)
    # assert tr.value == upvalue
    assert tr.commission == commission + upcomm

    size = tr.size
    price = tr.price
    commission = tr.commission

    upsize = -size
    upprice = 12.5
    upvalue = upsize * upprice
    upcomm = abs(value) * commrate

    tr.update(order=order, size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0, comminfo=FakeCommInfo())

    assert tr.isclosed
    assert tr.size == size + upsize
    assert tr.price == price  # no change ... we simple closed the operation
    # assert tr.value == upvalue
    assert tr.commission == commission + upcomm


if __name__ == '__main__':
    test_run(main=True)
