#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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

import math

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase


class Returns(TimeFrameAnalyzerBase):
    '''Total, Average, Compound and Annualized Returns calculated using a
    logarithmic approach

    See:

      - https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

    Params:

      - ``timeframe`` (default: ``None``)

        If ``None`` the ``timeframe`` of the 1st data in the system will be
        used

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - ``tann`` (default: ``None``)

        Number of periods to use for the annualization (normalization) of the

        namely:

          - ``days: 252``
          - ``weeks: 52``
          - ``months: 12``
          - ``years: 1``

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys

        The returned dict the following keys:

          - ``rtot``: Total compound return
          - ``ravg``: Average return for the entire period (timeframe specific)
          - ``rnorm``: Annualized/Normalized return
          - ``rnorm100``: Annualized/Normalized return expressed in 100%

    '''

    params = (
        ('tann', None),
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def start(self):
        super(Returns, self).start()
        self._value_start = self.strategy.broker.getvalue()
        self._tcount = 0

    def stop(self):
        super(Returns, self).stop()

        self._value_end = self.strategy.broker.getvalue()

        # Compound return
        self.rets['rtot'] = rtot = (
            math.log(self._value_end / self._value_start))

        # Average return
        self.rets['ravg'] = ravg = rtot / self._tcount

        # Annualized normalized return
        tann = self.p.tann or self._TANN.get(self.timeframe, None)
        if tann is None:
            tann = self._TANN.get(self.data._timeframe, 1.0)  # assign default

        self.rets['rnorm'] = rnorm = math.expm1(ravg * tann)
        self.rets['rnorm100'] = rnorm * 100.0  # human readable %

    def _on_dt_over(self):
        self._tcount += 1  # count the subperiod
