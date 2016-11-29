#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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

import backtrader as bt

class Vortex(bt.Indicator):
    '''
    See:
      - http://www.vortexindicator.com/VFX_VORTEX.PDF

    Params
      - ``period``
    '''
    params = (('period', 14),)

    lines = ('vi_plus', 'vi_minus',)

    def __init__(self):
        vm_plus = bt.ind.SumN(abs(self.data.high(0) - self.data.low(-1)), period=self.p.period)
        vm_minus = bt.ind.SumN(abs(self.data.low(0) - self.data.high(-1)), period=self.p.period)
        tr = bt.ind.SumN(bt.Max(
            self.data.high(0) - self.data.low(0),
            abs(self.data.high(0) - self.data.close(-1)),
            abs(self.data.low(0) - self.data.close(-1))), period=self.p.period)

        self.l.vi_plus = vm_plus / tr
        self.l.vi_minus = vm_minus / tr
