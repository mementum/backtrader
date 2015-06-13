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

from .. import LineObserver, ObserverPot
from ..datapos import Operation


class _OperationsPnLObserver(LineObserver):
    lines = ('pnl',)

    plotinfo = dict(
        plotname='Operation Gross Profit/Loss',
        plothlines=[0.0])
    plotlines = dict(
        pnl=dict(marker='o', color='blue', markersize=8.0, fillstyle='full'))

    def __init__(self, dataidx):
        self.data = self.datas[dataidx]
        self.operation = Operation()
        self.operations = list()

    def next(self):
        for order in self._owner._orderspending:
            if order.data is not self.data or not order.executed.size:
                continue

            for exbit in order.executed.exbits:
                self.operation.update(exbit.closed,
                                      exbit.price,
                                      exbit.closedvalue,
                                      exbit.closedcomm)
                if self.operation.isclosed:
                    # operation closed, record the pnl
                    self.lines.pnl[0] = self.operation.pnl
                    self.operations.append(self.operation)

                    # Open the next operation
                    self.operation = Operation()

                # Updated
                self.operation.update(exbit.opened,
                                      exbit.price,
                                      exbit.openedvalue,
                                      exbit.openedcomm)


class OperationsPnLObserver(ObserverPot):
    _ObserverCls = _OperationsPnLObserver
