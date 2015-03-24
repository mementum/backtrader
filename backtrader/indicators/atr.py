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

from .. import DataSeries, Indicator
from .ma import MATypes
from .linesutils import LinesDifference, LinesMax


class TR(Indicator):
    lines = ('tr',)

    def __init__(self):
        hl = LinesDifference(self.data, line=DataSeries.High, line1=DataSeries.Low)
        hc = LinesDifference(self.data, line=DataSeries.High, line1=DataSeries.Close, ago1=1)
        cl = LinesDifference(self.data, line=DataSeries.Close, ago=1, line1=DataSeries.Low)

        LinesMax(hl, LinesMax(hc, cl)).bindlines('tr')


class TrueRange(TR):
    pass


class ATR(Indicator):
    lines = ('atr',)
    params = (('period', 14), ('matype', MATypes.Simple))

    def _plotlabel(self):
        plabels = [self.p.period,]
        if self.p.matype != MATypes.Simple:
            plabels += [self.params.matype.__name__,]
        return ','.join(map(str, plabels))

    def __init__(self):
        self.p.matype(TR(self.data), period=self.p.period).bind2lines('atr')


class AverageTrueRange(ATR):
    pass
