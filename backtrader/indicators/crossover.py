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

from . import Indicator, And


class _CrossBase(Indicator):
    _mindatas = 2

    lines = ('cross',)

    plotinfo = dict(plotymargin=0.05, plotyhlines=[0.0, 1.0])

    def __init__(self):
        if self._crossup:
            before = self.data0(-1) < self.data1(-1)
            after = self.data0 > self.data1
        else:
            before = self.data0(-1) > self.data1(-1)
            after = self.data0 < self.data1

        self.lines.cross = And(before, after)


class CrossUp(_CrossBase):
    '''
    This indicator gives a signal if the 1st provided data crosses over the 2nd
    indicator upwards

    It does need to look into the current time index (0) and the previous time
    index (-1) of both the 1t and 2nd data

    This indicator is not automatically plotted

    Formula:
      - upcross = data0(-1) < data1(-1) and data0(0) > data1(0)
    '''
    _crossup = True


class CrossDown(_CrossBase):
    '''
    This indicator gives a signal if the 1st provided data crosses over the 2nd
    indicator upwards

    It does need to look into the current time index (0) and the previous time
    index (-1) of both the 1t and 2nd data

    This indicator is not automatically plotted

    Formula:
      - upcross = data0(-1) < data1(-1) and data0(0) > data1(0)
    '''
    _crossup = False


class CrossOver(Indicator):
    '''
    This indicator gives a signal if the provided datas (2) cross up or down.

      - 1.0 if the 1st data crosses the 2nd data upwards
      - -1.0 if the 1st data crosses the 2nd data downwards

    It does need to look into the current time index (0) and the previous time
    index (-1) of both the 1t and 2nd data

    This indicator is not automatically plotted

    Formula:
      - upcross = data0(-1) < data1(-1) and data0(0) > data1(0)
      - downcross = data0(-1) > data1(-1) and data0(0) < data1(0)
      - crossover = upcross - downcross
    '''
    _mindatas = 2

    lines = ('crossover',)

    plotinfo = dict(plotymargin=0.05, plotyhlines=[-1.0, 1.0])

    def __init__(self):
        upcross = CrossUp(self.data, self.data1)
        downcross = CrossDown(self.data, self.data1)

        self.lines.crossover = upcross - downcross
