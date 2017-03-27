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

import backtrader as bt
from . import TimeDrawDown


__all__ = ['Calmar']


class Calmar(bt.TimeFrameAnalyzerBase):
    '''This analyzer calculates the CalmarRatio
    timeframe which can be different from the one used in the underlying data
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
      - *None*

    See also:

      - https://en.wikipedia.org/wiki/Calmar_ratio

    Methods:
      - ``get_analysis``

        Returns a OrderedDict with a key for the time period and the
        corresponding rolling Calmar ratio

    Attributes:
      - ``calmar`` the latest calculated calmar ratio
    '''

    packages = ('collections', 'math',)

    params = (
        ('timeframe', bt.TimeFrame.Months),  # default in calmar
        ('period', 36),
    )

    def __init__(self):
        self._maxdd = TimeDrawDown(timeframe=self.p.timeframe,
                                   compression=self.p.compression)

    def start(self):
        self._mdd = float('-inf')
        self._values = collections.deque([float('Nan')] * self.p.period,
                                         maxlen=self.p.period)
        self._values.append(self.strategy.broker.getvalue())

    def on_dt_over(self):
        self._mdd = max(self._mdd, self._maxdd.maxdd)
        self._values.append(self.strategy.broker.getvalue())
        rann = math.log(self._values[-1] / self._values[0]) / len(self._values)
        self.calmar = calmar = rann / (self._mdd or float('Inf'))

        self.rets[self.dtkey] = calmar

    def stop(self):
        self.on_dt_over()  # update last values
