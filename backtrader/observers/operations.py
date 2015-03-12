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

from .. import lineiterator
from ..datapos import Operation


class OperationsPnLObserver(object):
    def __init__(self, datas):
        for data in datas:
            _OperationsPnLObserver(data)


class _OperationsPnLObserver(lineiterator.LineObserver):
    lines = ('pnl',)

    plotinfo = dict(
        pnl=dict(marker='o', markersize=8.0, fillstyle='none',),
    )

    def __init__(self):
        self.data = self.datas[0]
        self.operation = Operation()

    def next(self):
        for order in self._owner._orderspending:
            if order.data != self.data or not order.executed.size:
                continue

            for exbit in order.executed.exbits:
                self.operation.update(exbit.closed, exbit.price, exbit.closedvalue, exbit.closedcomm)
                if not self.operation:
                    # operation closed, record the pnl
                    self.lines.pnl = self.operation.pnl

                    # Open the next operation
                    self.operation = Operation()

                # Updated
                self.operation.update(exbit.opened, exbit.price, exbit.openedvalue, exbit.openedcomm)
