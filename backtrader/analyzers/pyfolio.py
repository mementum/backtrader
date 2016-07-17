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

from backtrader import Analyzer
from backtrader.utils.py3 import items, iteritems

from . import TimeReturn, PositionsValue, Transactions, GrossLeverage


class PyFolio(Analyzer):
    '''
    This analyzer reports the positions of the current set of datas

    Params:

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = ()

    def __init__(self):
        self._returns = TimeReturn()
        self._positions = PositionsValue(headers=True, cash=True)
        self._transactions = Transactions(headers=True)
        self._gross_lev = GrossLeverage()

    def stop(self):
        super(PyFolio, self).stop()
        self.rets['returns'] = self._returns.get_analysis()
        self.rets['positions'] = self._positions.get_analysis()
        self.rets['transactions'] = self._transactions.get_analysis()
        self.rets['gross_lev'] = self._gross_lev.get_analysis()

    def get_pf_items(self):
        # keep import local to avoid disturbing installations with no pandas
        import pandas
        from pandas import DataFrame as DF

        #
        # Returns
        cols = ['index', 'return']
        returns = DF.from_records(iteritems(self.rets['returns']),
                                  index=cols[0], columns=cols)
        returns.index = pandas.to_datetime(returns.index)
        returns.index = returns.index.tz_localize('UTC')
        returns = returns['return']
        #
        # Positions
        pss = self.rets['positions']
        ps = [[k] + v for k, v in iteritems(pss)]
        cols = ps.pop(0)
        positions = DF.from_records(ps, index=cols[0], columns=cols)
        positions.index = pandas.to_datetime(positions.index)
        positions.index = positions.index.tz_localize('UTC')

        #
        # Transactions
        txss = self.rets['transactions']
        txs = list()
        for k, v in iteritems(txss):
            for v2 in v:
                txs.append([k] + v2)

        # txs = [[k] + v for k, v in iteritems(txss)]
        cols = txs.pop(0)
        transactions = DF.from_records(txs, index=cols[0], columns=cols)
        transactions.index = pandas.to_datetime(transactions.index)
        transactions.index = transactions.index.tz_localize('UTC')

        # Gross Leverage
        cols = ['index', 'gross_lev']
        gross_lev = DF.from_records(iteritems(self.rets['gross_lev']),
                                    index=cols[0], columns=cols)

        gross_lev.index = pandas.to_datetime(gross_lev.index)
        gross_lev.index = gross_lev.index.tz_localize('UTC')
        gross_lev = gross_lev['gross_lev']

        # Return all together
        return returns, positions, transactions, gross_lev
