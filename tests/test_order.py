#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
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
from backtrader import Order, Position


class FakeCommInfo(object):
    def getvaluesize(self, size, price):
        return 0

    def profitandloss(self, size, price, newprice):
        return 0

    def getoperationcost(self, size, price):
        return 0.0

    def getcommission(self, size, price):
        return 0.0


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


def _execute(position, order, size, price, partial):
    # Find position and do a real update - accounting happens here
    pprice_orig = position.price
    psize, pprice, opened, closed = position.update(size, price)

    comminfo = order.comminfo
    closedvalue = comminfo.getoperationcost(closed, pprice_orig)
    closedcomm = comminfo.getcommission(closed, price)

    openedvalue = comminfo.getoperationcost(opened, price)
    openedcomm = comminfo.getcommission(opened, price)

    pnl = comminfo.profitandloss(-closed, pprice_orig, price)
    margin = comminfo.getvaluesize(size, price)

    order.execute(order.data.datetime[0],
                  size, price,
                  closed, closedvalue, closedcomm,
                  opened, openedvalue, openedcomm,
                  margin, pnl,
                  psize, pprice)  # pnl

    if partial:
        order.partial()
    else:
        order.completed()


def test_run(main=False):
    position = Position()
    comminfo = FakeCommInfo()
    order = bt.BuyOrder(data=FakeData(),
                        size=100, price=1.0,
                        exectype=bt.Order.Market,
                        simulated=True)
    order.addcomminfo(comminfo)

    ### Test that partially updating order will maintain correct iterpending sequence
    ### (Orders are cloned for each notification. The pending bits should be reported
    ###  related to the previous notification (clone))

    # Add two bits and validate we have two pending bits
    _execute(position, order, 10, 1.0, True)
    _execute(position, order, 20, 1.1, True)

    clone = order.clone()
    pending = clone.executed.getpending()
    assert len(pending) == 2
    assert pending[0].size == 10
    assert pending[0].price == 1.0
    assert pending[1].size == 20
    assert pending[1].price == 1.1

    # Add additional two bits and validate we still have two pending bits after clone
    _execute(position, order, 30, 1.2, True)
    _execute(position, order, 40, 1.3, False)

    clone = order.clone()
    pending = clone.executed.getpending()
    assert len(pending) == 2
    assert pending[0].size == 30
    assert pending[0].price == 1.2
    assert pending[1].size == 40
    assert pending[1].price == 1.3

if __name__ == '__main__':
    test_run(main=True)
