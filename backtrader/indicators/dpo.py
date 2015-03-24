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

from .. import Indicator
from .ma import MATypes
from .linesutils import LinesDiff


class DPO(Indicator):
    # Named output lines
    lines = ('dpo',)

    # Accepted parameters (and defaults) - MovAvg also parameter to allow experimentation
    params = (('period', 20), ('line', Indicator.Close), ('matype', MATypes.Simple),)

    # Emphasize central 0.0 line in plot
    plotinfo = dict(hlines=[0.0,],)

    # Indicator information after the name (in brackets)
    def _plotlabel(self):
        plabels = [self.p.period,]
        if self.p.matype != MATypes.Simple:
            plabels += [self.params.matype.__name__]
        return ','.join(map(str, plabels))

    def __init__(self):
        # Create the Moving Average
        ma = self.p.matype(self.data, line=self.p.line, period=self.p.period)

        # Calculate the value (look back ago1 in MovAvg)  and bind it to the output 'dpo' line
        LinesDiff(self.data, ma, line=self.p.line, ago1=self.p.period // 2 + 1).bind2lines('dpo')


# Alias for DPO
class DetrendedPriceOscillator(DPO):
    pass
