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

from __future__ import absolute_import, division, print_function, unicode_literals

from .. import Indicator
from .ma import MATypes
from .utils import LineDifference


class DetrendedPriceOscillator(Indicator):
    lines = ('dpo',)
    params = (('period', 20), ('line', 0), ('matype', MATypes.Simple),)

    plotinfo = dict(plotname='DPO', hlines=[0.0,],)

    def _plotlabel(self):
        plabels = [self.params.period,]
        return ','.join(map(str, plabels))

    def __init__(self):
        ma = self.params.matype(self.datas[0], period=self.params.period, line=self.params.line)
        shift = self.params.period // 2 + 1
        LineDifference(self.datas[0], ma, line0=self.params.line, ago1=-shift).bindlines(0)
        self.setminperiod(shift)


DPO = DetrendedPriceOscillator
