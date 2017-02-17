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

from . import Indicator

__all__ = ['LaguerreRSI']

class LaguerreRSI(Indicator):
    alias = ('LRSI',)
    lines = ('lrsi',)
    params = (('gamma', 0.5),)

    plotinfo = dict(
        plotymargin=0.15,
        plotyticks=[0.0, 0.2, 0.5, 0.8, 1.0]
    )

    def __init__(self):
        self.addminperiod(6)
        self.l0 = [0, 0]
        self.l1 = [0, 0]
        self.l2 = [0, 0]
        self.l3 = [0, 0]

        super(LaguerreRSI, self).__init__()

    def next(self):
        tp = (self.data.high + self.data.low) / 2
        self.l0.insert(0, ((1 - self.p.gamma) * tp +
                           self.p.gamma * self.l0[0]))
        self.l1.insert(0, (-self.p.gamma * self.l0[0] + self.l0[1] +
                           self.p.gamma * self.l1[0]))
        self.l2.insert(0, (-self.p.gamma * self.l1[0] + self.l1[1] +
                           self.p.gamma * self.l2[0]))
        self.l3.insert(0, (-self.p.gamma * self.l2[0] + self.l2[1] +
                           self.p.gamma * self.l3[0]))
        del self.l0[2:]
        del self.l1[2:]
        del self.l2[2:]
        del self.l3[2:]

        cd = 0
        cu = 0
        if self.l0[0] >= self.l1[0]:
            cu = self.l0[0] - self.l1[0]
        else:
            cd = self.l1[0] - self.l0[0]

        if self.l1[0] >= self.l2[0]:
            cu = cu + self.l1[0] - self.l2[0]
        else:
            cd = cd + self.l2[0] - self.l1[0]

        if self.l2[0] >= self.l3[0]:
            cu = cu + self.l2[0] - self.l3[0]
        else:
            cd = cd + self.l3[0] - self.l2[0]

        self.lines.lrsi[0] = cu / (cu + cd)
