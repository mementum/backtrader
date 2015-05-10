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

from .. indicator import Indicator
from .ma import MovAv


class MACD(Indicator):
    lines = ('macd', 'signal',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9),
              ('movav', MovAv.Exponential),)

    plotinfo = dict(plothlines=[0.0])
    plotlines = dict(signal=dict(ls='--'))

    def _plotlabel(self):
        plabels = super(MACD, self)._plotlabel()
        if self.p.isdefault('movav'):
            plabels.remove(self.p.movav)
        return plabels

    def __init__(self):
        me1 = self.p.movav(self.data, period=self.p.period_me1)
        me2 = self.p.movav(self.data, period=self.p.period_me2)
        self.lines.macd = me1 - me2
        self.lines.signal = self.p.movav(self.lines.macd,
                                         period=self.p.period_signal)


class MACDHisto(MACD):
    lines = ('histo',)
    plotlines = dict(histo=dict(_method='bar', alpha=0.50, width=1.0))

    def __init__(self):
        super(MACDHisto, self).__init__()
        self.lines.histo = self.lines.macd - self.lines.signal
