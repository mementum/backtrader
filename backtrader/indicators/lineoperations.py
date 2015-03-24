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


from .. import Indicator
from .lineutils import _SingleLineBase


class _LineValOperation(_SingleLineBase):
    def __init__(self, *args):
        self.val = args[0]


class MultVal(_LineValOperation):
    def next(self):
        self.lines[0] = self.dline[self.p.ago] * self.val

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        val = self.val

        for i in xrange(start, end):
            larray[i] = darray[i - ago] * val


class DivVal(MultVal):
    def __init__(self, *args):
        self.val = 1.0 / self.val


class ValDiv(_LineValOperation):
    def next(self):
        self.lines[0] = self.val / self.dline[self.p.ago]

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        val = self.val

        for i in xrange(start, end):
            larray[i] = val / darray[i - ago]


class PlusVal(_LineValOperation):
    def next(self):
        self.lines[0] = self.dlines[self.p.ago] + self.val

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        val = self.val

        for i in xrange(start, end):
            larray[i] = darray[i - ago] + val


class MinusVal(_LineValOperation):
    def next(self):
        self.lines[0] = self.dlines[self.p.ago] - self.val

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        val = self.val

        for i in xrange(start, end):
            larray[i] = darray[i - ago] - val


class ValMinus(_LineValOperation):
    def next(self):
        self.lines[0] = self.val - self.dlines[self.p.ago]

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        val = self.val

        for i in xrange(start, end):
            larray[i] = val - darray[i - ago]


class MaxVal(_LineValOperation):
    def next(self):
        self.lines[0] = max(self.dlines[self.p.ago], self.val)

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        val = self.val

        for i in xrange(start, end):
            larray[i] = max(darray[i - ago], val)
