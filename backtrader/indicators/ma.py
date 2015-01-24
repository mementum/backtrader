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
import collections
import math

from .. import Indicator


class MovingAverageSimple(Indicator):
    lines = ('avg',)
    params = (('period', 30), ('line', 0))

    def __init__(self):
        self.dataline = self.datas[0][self.params.line]
        self.fperiod = float(self.params.period)
        self.setminperiod(self.params.period)

        self.dq = collections.deque(maxlen=self.params.period)

    def prenext(self):
        self.dq.append(self.dataline[0])

    def next(self):
        self.dq.append(self.dataline[0])
        self.lines[0][0] = math.fsum(self.dq) / self.fperiod


class MovingAverageWeighted(MovingAverageSimple):
    def __init__(self):
        self.weights = map(float, range(1, self.params.period + 1))
        self.coef = 2.0 / (self.fperiod * (self.fperiod + 1.0))

    def next(self):
        self.dq.append(self.dataline[0])
        self.lines[0][0] = self.coef * sum(map(operator.mul, self.dq, self.weights))


class MovingAverageSmoothing(MovingAverageSimple):
    def nextstart(self):
        # Let MovingAverageSimple produce the 1st value
        super(MovingAverageSmoothing, self).next()

    def next(self):
        previous = self.lines[0][1] * (1.0 - self.smoothfactor)
        current = self.dataline[0] * self.smoothfactor
        self.lines[0][0] = previous + current


class MovingAverageExponential(MovingAverageSmoothing):
    def __init__(self):
        self.smoothfactor = 2.0 / (1.0 + self.fperiod)


class MovingAverageSmoothed(MovingAverageSmoothing):
    def __init__(self):
        self.smoothfactor = 1.0 / self.fperiod


class MAType(object):
    Simple, Exponential, Smoothed, Weighted = range(4)


class MAClass(object):
    classes = (MovingAverageSimple,
               MovingAverageExponential,
               MovingAverageSmoothed,
               MovingAverageWeighted,)

    def __new__(cls, clstype):
        return cls.classes[clstype]


class MATypes(object):
    Simple = MovingAverageSimple
    Exponential = MovingAverageExponential
    Smoothed = MovingAverageSmoothed
    Weighted = MovingAverageWeighted
