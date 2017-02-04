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

import backtrader as bt


class FixedSize(bt.Sizer):
    '''This sizer simply returns a fixed size for any operation

    Params:
      - ``stake`` (default: ``1``)
    '''

    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        return self.params.stake

    def setsizing(self, stake):
        self.p.stake = stake  # OLD METHOD FOR SAMPLE COMPATIBILITY


SizerFix = FixedSize


class FixedReverser(bt.Sizer):
    '''This sizer returns the needes fixed size to reverse an open position or
    the fixed size to open one

      - To open a position: return the param ``stake``

      - To reverse a position: return 2 * ``stake``

    Params:
      - ``stake`` (default: ``1``)
    '''
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.strategy.getposition(data)
        size = self.p.stake * (1 + (position.size != 0))
        return size
