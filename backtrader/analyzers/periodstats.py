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
from . import TimeReturn


__all__ = ['PeriodStats']


class PeriodStats(bt.Analyzer):
    '''Calculates basic statistics for given timeframe

    ``get_analysis`` returns a dictionary containing the keys:

      - ``average``
      - ``stddev``
      - ``positive``
      - ``negative``
      - ``nochange``
      - ``best``
      - ``worst``

    If the parameter ``zeroispos`` is set to ``True``, periods with no change
    will be counted as positive
    '''

    params = (
        ('timeframe', bt.TimeFrame.Years),
        ('compression', 1),
        ('zeroispos', False),
    )

    def __init__(self):
        self._tr = TimeReturn(timeframe=self.p.timeframe,
                              compression=self.p.compression)

    def stop(self):
        trets = self._tr.get_analysis()  # dict key = date, value = ret
        pos = nul = neg = 0
        trets = list(itervalues(trets))
        for tret in trets:
            if tret > 0.0:
                pos += 1
            elif tret < 0.0:
                neg += 1
            else:
                if self.p.zeroispos:
                    pos += tret == 0.0
                else:
                    nul += tret == 0.0

        self.rets['average'] = avg = average(trets)
        self.rets['stddev'] = standarddev(trets, avg)

        self.rets['positive'] = pos
        self.rets['negative'] = neg
        self.rets['nochange'] = nul

        self.rets['best'] = max(trets)
        self.rets['worst'] = min(trets)
