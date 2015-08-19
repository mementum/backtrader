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

import copy
import datetime
import itertools

import six

from .metabase import MetaParams
from .utils import date2num


class OrderExecutionBit(object):
    def __init__(self,
                 dt=None, size=0, price=0.0,
                 closed=0, closedvalue=0.0, closedcomm=0.0,
                 opened=0, openedvalue=0.0, openedcomm=0.0,
                 pnl=0.0,
                 psize=0, pprice=0.0):

        self.dt = dt
        self.size = size
        self.price = price

        self.closed = closed
        self.opened = opened
        self.closedvalue = closedvalue
        self.openedvalue = openedvalue
        self.closedcomm = closedcomm
        self.openedcomm = openedcomm

        self.value = closedvalue + openedvalue
        self.comm = closedcomm + openedcomm
        self.pnl = pnl

        self.psize = psize
        self.pprice = pprice


class OrderData(object):
    def __init__(self, dt=None, size=0, price=0.0, pricelimit=0.0, remsize=0):
        self.exbits = list()

        self.dt = dt
        self.size = size
        self.remsize = remsize
        self.price = price
        self.pricelimit = pricelimit

        if not pricelimit:
            # if no pricelimit is given, use the given price
            self.pricelimit = self.price

        if pricelimit and not price:
            # price must always be set if pricelimit is set ...
            self.price = pricelimit

        self.value = 0.0
        self.comm = 0.0
        self.margin = None
        self.pnl = 0.0

        self.psize = 0
        self.pprice = 0

    def __len__(self):
        return len(self.exbits)

    def __getitem__(self, key):
        return self.exbits[key]

    def add(self, dt, size, price,
            closed, closedvalue, closedcommission,
            opened, openedvalue, openedcomm, pnl,
            psize, pprice):

        self.addbit(
            OrderExecutionBit(dt, size, price,
                              closed, closedvalue, closedcommission,
                              opened, openedvalue, openedcomm, pnl,
                              psize, pprice))

    def addbit(self, exbit):
        self.exbits.append(exbit)

        self.remsize -= exbit.size

        self.dt = exbit.dt
        oldvalue = self.size * self.price
        newvalue = exbit.size * exbit.price
        self.size += exbit.size
        self.price = (oldvalue + newvalue) / self.size
        self.value += exbit.value
        self.comm += exbit.comm
        self.pnl += exbit.pnl
        self.psize = exbit.psize
        self.pprice = exbit.pprice


class Order(six.with_metaclass(MetaParams, object)):
    refbasis = itertools.count(1)

    Market, Close, Limit, Stop, StopLimit = range(5)

    Buy, Sell = range(2)

    Submitted, Accepted, Partial, Completed, \
        Canceled, Expired, Margin = range(7)

    Status = [
        'Submitted', 'Accepted', 'Partial',
        'Completed', 'Canceled', 'Expired', 'Margin'
    ]

    params = (
        ('owner', None), ('data', None), ('size', None), ('price', None),
        ('pricelimit', None), ('exectype', None), ('valid', None),
        ('triggered', False),
    )

    def __getattr__(self, name):
        # dig into self.params if not found as attribute
        # mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            setattr(self.params, name, value)
        else:
            super(Order, self).__setattribute__(name, value)

    def __eq__(self, other):
        return self.ref == other.ref

    def __ne__(self, other):
        return self.ref != other.ref

    def __init__(self):
        self.ref = next(self.refbasis)

        if self.params.exectype is None:
            self.params.exectype = Order.Market

        self.status = Order.Submitted
        if not self.isbuy():
            self.params.size = -self.params.size

        # Set a reference price if price is not set using
        # the close price
        if not self.p.price and not self.p.pricelimit:
            price = self.data.close[0]
        else:
            price = self.p.price

        self.created = OrderData(dt=self.data.datetime[0],
                                 size=self.params.size,
                                 price=price,
                                 pricelimit=self.params.pricelimit)

        self.executed = OrderData(remsize=self.params.size)
        self.position = 0

        if isinstance(self.p.valid, (datetime.datetime, datetime.date)):
            # comparison will later be done against the raw datetime[0] value
            self.p.valid = date2num(self.p.valid)

        # get next session end
        dtime = self.data.datetime.datetime(0)

        # provisional end-of-session
        session = self.data.p.sessionend
        h, m, s = session.hour, session.minute, session.second
        dteos = dtime.replace(hour=h, minute=m, second=s)

        if dteos < dtime:
            # eos before current time ... no ... must be next day
            dteos += datetime.timedelta(days=1)

        self.dteos = date2num(dteos)

    def clone(self):
        obj = copy.copy(self)
        obj.executed = copy.deepcopy(self.executed)
        return obj

    def setposition(self, position):
        self.position = position

    def isbuy(self):
        return isinstance(self, BuyOrder)

    def issell(self):
        return isinstance(self, SellOrder)

    def accept(self):
        self.status = Order.Accepted

    def cancel(self):
        self.status = Order.Canceled
        self.executed.dt = self.data.datetime[0]

    def execute(self, dt, size, price,
                closed, closedvalue, closedcomm,
                opened, openedvalue, openedcomm,
                margin, pnl,
                psize, pprice):

        if not size:
            return

        self.executed.add(dt, size, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          pnl, psize, pprice)

        self.executed.margin = margin
        if self.executed.remsize:
            self.status = Order.Partial
        else:
            self.status = Order.Completed

    def expire(self):
        if self.params.exectype == Order.Market:
            return False  # will be executed yes or yes

        if self.valid and self.data.datetime[0] > self.valid:
            self.status = Order.Expired
            self.executed.dt = self.data.datetime[0]
            return True

        return False

    def margin(self):
        self.status = Order.Margin
        self.executed.dt = self.data.datetime[0]

    def alive(self):
        return self.status in [Order.Partial, Order.Accepted]


class BuyOrder(Order):
    ordtype = Order.Buy


class StopBuyOrder(BuyOrder):
    pass


class StopLimitBuyOrder(BuyOrder):
    pass


class SellOrder(Order):
    ordtype = Order.Sell


class StopSellOrder(SellOrder):
    pass


class StopLimitSellOrder(SellOrder):
    pass
