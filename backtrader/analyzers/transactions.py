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


import collections

from backtrader import Order, Position, TimeFrameAnalyzerBase


class Transactions(TimeFrameAnalyzerBase):
    '''This analyzer reports the transactions occurred with each an every data in
    the system

    It looks at the order execution bits to create a ``Position`` starting from
    0 during each ``next`` cycle.

    The result is used during next to record the transactions

    Params:

      - timeframe (default: ``None``)
        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - headers (default: ``True``)

        Add an initial key to the dictionary holding the results with the names
        of the datas

        This analyzer was modeled to facilitate the integration with
        ``pyfolio`` and the header names are taken from the samples used for
        it::

          'date', 'amount', 'price', 'sid', 'symbol', 'value'

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('headers', False),
    )

    def start(self):
        super(Transactions, self).start()
        if self.p.headers:
            self.rets['date'] = [['amount', 'price', 'sid', 'symbol', 'value']]

        self._positions = collections.defaultdict(Position)

    def notify_order(self, order):
        # An order could have several partial executions per cycle (unlikely
        # but possible) and therefore: collect each new execution notification
        # and let the work for next

        # We use a fresh Position object for each round to get summary of what
        # the execution bits have done in that round
        if order.status not in [Order.Partial, Order.Completed]:
            return  # It's not an execution

        dname = order.data._name
        for exbit in order.executed.iterpending():
            if exbit is None:
                break  # end of pending reached

            self._positions[dname].update(exbit.size, exbit.price)

    def next(self):
        super(Transactions, self).next()  # let dtkey update
        # Updates the positions for "dtkey" (see base class) for each cycle
        entries = list()
        for i, dname in enumerate(self.strategy.getdatanames()):
            pos = self._positions.get(dname, None)
            if pos is None:
                continue
            size, price = pos.size, pos.price
            if not size:
                continue

            entries.append([size, price, i, dname, -size * price])

        if entries:  # only add if something was added
            self.rets[self.dtkey] = entries
        else:
            # remove any previous positions if None are there
            self.rets.pop(self.dtkey, None)

        self._positions.clear()
