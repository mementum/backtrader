#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2021-2025 Brian Mello
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

import backtrader as bt
from backtrader import Order, Position
from backtrader.utils.autodict import AutoOrderedDict


class Indicators(bt.Analyzer):
    '''This analyzer reports the transactions occurred with each an every data in
    the system

    It looks at the order execution bits to create a ``Position`` starting from
    0 during each ``next`` cycle.

    The result is used during next to record the transactions

    Params:

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
        ('log_by_order', False)
    )

    def _get_data_header(self):
            headers = ['datetime', 'dataname', 'open', 'high', 'low', 'close', 'volume']

            ind_headers = [ind.plotinfo.plotname.split('_')[0] for ind in self.strategy.getindicators_lines()]

            ind_headers = list(set(ind_headers))

            headers.extend(ind_headers)

            return headers

    def start(self):
        super().start()
        if self.p.headers:
            headers= self._get_data_header()
            self.rets[headers[0]] = [list(headers[1:])]

        self._data_factors = list()
        #self._idnames = list(enumerate(self.strategy.getdatanames()))

    def notify_order(self, order):
        # An order could have several partial executions per cycle (unlikely
        # but possible) and therefore: collect each new execution notification
        # and let the work for next

        # We use a fresh Position object for each round to get summary of what
        # the execution bits have done in that round
        if order.status not in [Order.Partial, Order.Completed]:
            return  # It's not an execution

        self._data_factors.append(order.data)

    def next(self):

        if self.p.log_by_order:
            if len(self._data_factors) > 0:
                for data in self._data_factors:
                    self.log_entry(data)

                self._data_factors.clear()
        else:
            for data in self.datas:
                    self.log_entry(data)

    def _get_entry_line(self, data):
        #str(num2date(data.datetime[0]))
        line = [data.dataname,
                data.open[0],
                data.high[0],
                data.low[0],
                data.close[0],
                data.volume[0]]
        for ind in self.strategy.getindicators_lines():
            
            if data.dataname in ind.plotinfo.plotname:
                line.append(f"{ind+0}")

        return line

    def log_entry(self, data):
        dt = self.strategy.datetime.datetime()
        if dt not in self.rets:
            self.rets[dt] = list()
        self.rets[dt].append(self._get_entry_line(data))
