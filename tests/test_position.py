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
from backtrader import position


def test_run(main=False):
    size = 10
    price = 10.0

    pos = position.Position(size=size, price=price)
    assert pos.size == size
    assert pos.price == price

    upsize = 5
    upprice = 12.5
    nsize, nprice, opened, closed = pos.update(size=upsize, price=upprice)

    if main:
        print('pos.size/price', pos.size, pos.price)
        print('nsize, nprice, opened, closed', nsize, nprice, opened, closed)

    assert pos.size == size + upsize
    assert pos.size == nsize
    assert pos.price == ((size * price) + (upsize * upprice)) / pos.size
    assert pos.price == nprice
    assert opened == upsize
    assert not closed

    size = pos.size
    price = pos.price
    upsize = -7
    upprice = 14.5

    nsize, nprice, opened, closed = pos.update(size=upsize, price=upprice)

    if main:
        print('pos.size/price', pos.size, pos.price)
        print('nsize, nprice, opened, closed', nsize, nprice, opened, closed)

    assert pos.size == size + upsize

    assert pos.size == nsize
    assert pos.price == price
    assert pos.price == nprice
    assert not opened
    assert closed == upsize  # the closed must have the sign of "update" size

    size = pos.size
    price = pos.price
    upsize = -15
    upprice = 17.5

    nsize, nprice, opened, closed = pos.update(size=upsize, price=upprice)

    if main:
        print('pos.size/price', pos.size, pos.price)
        print('nsize, nprice, opened, closed', nsize, nprice, opened, closed)

    assert pos.size == size + upsize
    assert pos.size == nsize
    assert pos.price == upprice
    assert pos.price == nprice
    assert opened == size + upsize
    assert closed == -size


if __name__ == '__main__':
    test_run(main=True)
