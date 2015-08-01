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

import six

from .observer import LineObserver
from .observers import BuySellObserver
from .observers import CashValueObserver
from .observers import OperationsPnLObserver
from .observers import DrawDownObserver


class Analyzer(LineObserver):
    plotinfo = dict(plot=False, plotskip=True)

    params = dict(
        plotcashvalue=True,
        plotdrawdown=True,
        plotoperations=True,
        plotbuysell=True,
    )

    def __init__(self, *args, **kwargs):
        self._cashvalue = CashValueObserver(plot=self.p.plotcashvalue)
        self.cash = self._cashvalue.lines.cash
        self.value = self._cashvalue.lines.value

        self._drawdown = DrawDownObserver(plot=self.p.plotdrawdown)
        self.drawdown = self._drawdown.lines.drawdown
        self.maxdrawdown = self._drawdown.lines.maxdrawdown

        self._operations = OperationsPnLObserver(plot=self.p.plotcashvalue)
        self._buysell = BuySellObserver(plot=self.p.plotbuysell)
