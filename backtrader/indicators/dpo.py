#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################
# Python 2/3 compatibility imports
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import DataSeries, Indicator
from .ma import MATypes
from .utils import LineDifference


class DPO(Indicator):
    # Named output lines
    lines = ('dpo',)

    # Accepted parameters (and defaults) - Moving Average Type also a parameter
    params = (('period', 20), ('line', DataSeries.Close), ('matype', MATypes.Simple),)

    # Emphasize central 0.0 line in plot
    plotinfo = dict(hlines=[0.0,],)

    def _plotlabel(self):
        plabels = [self.params.period,]
        return ','.join(map(str, plabels))

    def __init__(self):
        # Create the Moving Average
        ma = self.params.matype(self.datas[0], line=self.params.line, period=self.params.period)

        # Calculate the backwards distance - // division ensures an int is returned
        shiftback = -(self.params.period // 2 + 1)

        # Calculate the value and bind it to the output 'dpo' line
        LineDifference(self.datas[0], ma, line0=self.params.line, ago1=shiftback).bind2lines('dpo')


# Alias for DPO
DetrendedPriceOscillator = DPO
