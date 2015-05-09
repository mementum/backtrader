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

from .. import Indicator
from .ma import MATypes
from .lineoperations import Max


class TR(Indicator):
    lines = ('tr',)

    def __init__(self):
        high = self.data[self.PriceHigh]
        low = self.data[self.PriceLow]
        close1 = self.data[self.PriceClose](-1)
        self.lines.tr = Max(high - low, abs(high - close1), abs(close1 - low))


class TrueRange(TR):
    pass  # alias


class ATR(Indicator):
    lines = ('atr',)
    params = (('period', 14), ('matype', MATypes.Simple))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.matype] * self.p.notdefault('matype')
        return plabels

    def __init__(self):
        self.lines.atr = self.p.matype(TR(self.data), period=self.p.period)


class AverageTrueRange(ATR):
    pass  # alias
