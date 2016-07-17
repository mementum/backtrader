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


from backtrader import TimeFrameAnalyzerBase


class PositionsValue(TimeFrameAnalyzerBase):
    '''
    This analyzer reports the positions of the current set of datas

    Params:

      - timeframe (default: ``None``)
        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - ``prenext`` (default: ``True``)
        Ideally a strategy shouldn't operate when the minimum period of the
        indicators has not yet been met and the method ``prenext`` is being
        called. But this is a *should* and not a prohibition.

        If this parameter is ``True`` the analyzer will report positions even
        during the ``prenext`` period

      - headers (default: ``True``)

        Add an initial key to the dictionary holding the results with the names
        of the datas

      - cash (default: ``True``)

        Include the actual cash as an extra position

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('prenext', True),
        ('headers',  False),
        ('cash', False),
    )

    def start(self):
        super(PositionsValue, self).start()
        if self.p.headers:
            headers = self.strategy.getdatanames() + ['cash'] * self.p.cash
            self.rets['Datetime'] = headers

    def prenext(self):
        if self.p.prenext():
            self.next()

    def next(self):
        if self._dt_over():
            pvals = [self.strategy.broker.get_value([d]) for d in self.datas]
            if self.p.cash:
                pvals.append(self.strategy.broker.get_cash())

            self.rets[self.dtkey] = pvals
