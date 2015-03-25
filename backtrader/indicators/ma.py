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
from .lineutils import SumAv, SumAvSmoothing, SumAvWeighted


class ExecOnces(Indicator):
    extralines = 1

    def prenext(self):
        pass # to avoid preonce be optimized away in metaclass

    def next(self):
        pass # to avoid once be optimized away in metaclass

    def preonce(self, start, end):
        self.data.preonce(start, end)
        self.data.preonce = self.data.once_empty

    def oncestart(self, start, end):
        self.data.oncestart(start, end)
        self.data.oncestart = self.data.once_empty

    def once(self, start, end):
        self.data.once = self.data.once_empty


class MovingAverageBase(Indicator):
    plotinfo = dict(subplot=False)

    def _plotlabel(self):
        return str(self.p.period)


class MovingAverageSimple(SumAv, MovingAverageBase):
    plotinfo = dict(plotname='SMA')


class MovingAverageExponential(SumAvSmoothing, MovingAverageBase):
    plotinfo = dict(plotname='EMA')

    def getsmoothfactor(self):
        return 2.0 / (1.0 + self.p.period)


class MovingAverageSmoothed(SumAvSmoothing, MovingAverageBase):
    plotinfo = dict(plotname='SMMA')

    def getsmoothfactor(self):
        return 1.0 / self.p.period


class MovingAverageWeighted(SumAvWeighted, MovingAverageBase):
    plotinfo = dict(plotname='WMA')


class MAEnum(object):
    Simple, Exponential, Smoothed, Weighted = range(4)


class MAClass(object):
    classes = (MovingAverageSimple,
               MovingAverageExponential,
               MovingAverageSmoothed,)

    def __new__(cls, clstype):
        return cls.classes[clstype]


class MATypes(object):
    Simple = MovingAverageSimple
    Exponential = MovingAverageExponential
    Smoothed = MovingAverageSmoothed
    Weighted = MovingAverageWeighted
