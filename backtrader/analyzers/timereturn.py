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

from backtrader import TimeFrameAnalyzerBase, TimeFrame


class TimeReturn(TimeFrameAnalyzerBase):
    '''
    This analyzer calculates the Returns by looking at the beginning
    and end of the timeframe

    Params:

      - timeframe (default: ``None``)
        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    def start(self):
        super(TimeReturn, self).start()
        self.lastvalue = self.strategy.broker.getvalue()

    def notify_cashvalue(self, cash, value):
        if self._dt_over():
            self.value_start = self.lastvalue  # last value before cycle change
            self.rets[self.dtkey] = (value / self.value_start) - 1.0

        self.lastvalue = value
