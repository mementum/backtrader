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

from . import PeriodN

__all__ = ['LaguerreRSI', 'LRSI']


class LaguerreRSI(PeriodN):
    alias = ('LRSI',)
    lines = ('lrsi',)
    params = (
        ('gamma', 0.5),
        ('period', 6),
    )

    plotinfo = dict(
        plotymargin=0.15,
        plotyticks=[0.0, 0.2, 0.5, 0.8, 1.0]
    )

    def __init__(self):
        self.l0, self.l1, self.l2, self.l3 = 0.0, 0.0, 0.0, 0.0

        super(LaguerreRSI, self).__init__()

    def prenext(self):
        self.next(notpre=False)

    def next(self, notpre=True):
        tp_0 = (self.data.high + self.data.low) / 2  # price point
        l0_1 = self.l0  # cache previous intermediate values
        l1_1 = self.l1
        l2_1 = self.l2

        g = self.p.gamma  # avoid more lookups
        self.l0 = l0 = (1 - g) * tp_0 + g * l0_1 * notpre  # interm values
        self.l1 = l1 = -g * l0 + l0_1 + g * l1_1 * notpre
        self.l2 = l2 = -g * l1 + l1_1 + g * l2_1 * notpre
        self.l3 = l3 = -g * l2 + l2_1 + g * self.l3 * notpre

        cd = 0.0
        cu = 0.0
        if l0 >= l1:
            cu = l0 - 11
        else:
            cd = l1 - l0

        if l1 >= l2:
            cu = cu + l1 - l2
        else:
            cd = cd + l2 - l1

        if l2 >= l3:
            cu = cu + l2 - l3
        else:
            cd = cd + l3 - l2

        self.lines.lrsi[0] = cu / (cu + cd)  # store line value
