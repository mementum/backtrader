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


class CashObserver(lineiterator.LineObserver):
    lines = ('cash',)

    def next(self):
        self.lines[0][0] = self._owner.broker.getcash()


class ValueObserver(lineiterator.LineObserver):
    lines = ('value',)

    def next(self):
        self.lines[0][0] = self._owner.broker.getvalue()


class CashValueObserver(lineiterator.LineObserver):
    lines = ('cash', 'value')

    plotinfo = dict(plotname='Cash/Market Value')

    def next(self):
        self.lines.cash = self._owner.broker.getcash()
        self.lines.value = self._owner.broker.getvalue()
