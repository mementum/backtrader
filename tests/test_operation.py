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

import testcommon

import backtrader as bt
from backtrader import datapos


def test_run(main=False):
    op = datapos.Operation(data=[None])

    commrate = 0.025
    size = 10
    price = 10.0
    value = size * price
    commission = value * commrate

    op.update(size=size, price=price, value=value,
              commission=commission, pnl=0.0)

    assert not op.isclosed
    assert op.size == size
    assert op.price == price
    assert op.value == value
    assert op.commission == commission
    assert not op.pnl
    assert not op.pnlcomm

    upsize = -5
    upprice = 12.5
    upvalue = upsize * upprice
    upcomm = abs(value) * commrate

    op.update(size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0)

    assert not op.isclosed
    assert op.size == size + upsize
    assert op.price == price  # size is being reduced, price must not change
    assert op.value == op.size * op.price
    assert op.commission == commission + upcomm

    size = op.size
    price = op.price
    commission = op.commission

    upsize = 7
    upprice = 14.5
    upvalue = upsize * upprice
    upcomm = abs(value) * commrate

    op.update(size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0)

    assert not op.isclosed
    assert op.size == size + upsize
    assert op.price == ((size * price) + (upsize * upprice)) / (size + upsize)
    assert op.value == op.size * op.price
    assert op.commission == commission + upcomm

    size = op.size
    price = op.price
    commission = op.commission

    upsize = -size
    upprice = 12.5
    upvalue = upsize * upprice
    upcomm = abs(value) * commrate

    op.update(size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0)

    assert op.isclosed
    assert op.size == size + upsize
    assert op.price == price  # no change ... we simple closed the operation
    assert op.value == op.size * op.price
    assert op.commission == commission + upcomm


if __name__ == '__main__':
    test_run(main=True)
