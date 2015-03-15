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

from .. import LineObserver


class CashObserver(LineObserver):
    lines = ('cash',)

    def next(self):
        self.lines[0][0] = self._owner.broker.getcash()


class ValueObserver(LineObserver):
    lines = ('value',)

    def next(self):
        self.lines[0][0] = self._owner.broker.getvalue()


class CashValueObserver(LineObserver):
    lines = ('cash', 'value')

    plotinfo = dict(plotname='Cash/Market Value')

    def __init__(self):
        self.maxdrawdown = 0.0
        self.peak = float('-inf')

    def next(self):
        self.lines.cash = self._owner.broker.getcash()
        self.lines.value = value = self._owner.broker.getvalue()

        # update the maximum seen peak
        if value > self.peak:
            self.peak = value

        # calculate the current drawdown
        drawdown = 100.0 * (self.peak - value) / self.peak

        # update the maxdrawdown if needed
        self.maxdrawdown = max(self.maxdrawdown, drawdown)
