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

import math

from six.moves import xrange

from .. import Indicator


class OperationN(Indicator):
    params = (('period', 1),)

    def __init__(self):
        self.addminperiod(self.p.period)

    def next(self):
        self.line[0] = self.func(self.data_0.get(size=self.p.period))

    def once(self, start, end):
        dst = self.line.array
        src = self.data_0.array
        period = self.p.period
        func = self.func

        for i in xrange(start, end):
            dst[i] = func(src[i - period + 1: i + 1])


class MaxN(OperationN):
    lines = ('maxn',)
    func = max


class Highest(OperationN):
    '''Highest

    Calculates the highest value for the data in a given period

    Formula:
      - highest = max(data, period)

    See:
      (None)

    Lines:
      - highest

    Params:
      - period (1): period for the operation
    '''
    lines = ('highest',)
    func = max


class MinN(OperationN):
    lines = ('minn',)
    func = min


class Lowest(OperationN):
    '''Lowest

    Calculates the lowest value for the data in a given period

    Formula:
      - lowest = min(data, period)

    See:
      (None)

    Lines:
      - lowest

    Params:
      - period (1): period for the operation
    '''
    lines = ('lowest',)
    func = min


class SumN(OperationN):
    '''SumN

    Calculates the Sum of the data values over a given period

    Formula:
      - sumn = sum(data, period)

    See:
      (None)

    Lines:
      - sumn

    Params:
      - period (1): period for the operation
    '''
    lines = ('sumn',)
    func = math.fsum
