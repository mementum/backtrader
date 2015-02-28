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
import operator

from .. import Indicator


class MovingAverageBase(Indicator):
    subplot = False

    def _plotlabel(self):
        return str(self.params.period)


class MovingAverageSimple(MovingAverageBase):
    lines = ('avg',)
    params = (('period', 30), ('line', 0))

    plotname = 'MA'

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

    def once(self, start, end):
        # Cache all dictionary accesses in local variables to speed up the loop
        fperiod = self.fperiod
        darray = self.dataline.array
        larray = self.lines[0].array
        mfsum = math.fsum

        for i in xrange(start, end):
            larray[i] = math.fsum(darray[i - period + 1, i + 1]) / self.fperiod

    def preonce_backup(self, start, end):
        for i in xrange(start, end):
            self.dq.append(self.dataline.array[i])

    def once_backup(self, start, end):
        # Cache all dictionary accesses in local variables to speed up the loop
        fperiod = self.fperiod
        dq = self.dq
        dqappend = dq.append
        darray = self.dataline.array
        larray = self.lines[0].array
        mfsum = math.fsum

        for i in xrange(start, end):
            dqappend(darray[i])
            larray[i] = mfsum(dq) / fperiod


class MovingAverageWeighted(MovingAverageSimple):
    plotname = 'WMA'

    def __init__(self):
        self.weights = map(float, range(1, self.params.period + 1))
        self.coef = 2.0 / (self.fperiod * (self.fperiod + 1.0))

    def next(self):
        self.dq.append(self.dataline[0])
        self.lines[0][0] = self.coef * sum(map(operator.mul, self.dq, self.weights))

    def once(self, start, end):
        # Cache all dictionary accesses in local variables to speed up the loop
        dq = self.dq
        dqappend = dq.append
        darray = self.dataline.array
        larray = self.lines[0].array
        opmul = operator.mul
        coef = self.coef
        weights = self.weights

        for i in xrange(start, end):
            dqappend(darray[i])
            larray[i] = coef * sum(map(opmul, dq, weights))


class MovingAverageSmoothing(MovingAverageSimple):
    def nextstart(self):
        # Let MovingAverageSimple produce the 1st value
        super(MovingAverageSmoothing, self).next()

    def next(self):
        previous = self.lines[0][-1] * (1.0 - self.smoothfactor)
        current = self.dataline[0] * self.smoothfactor
        self.lines[0][0] = previous + current

    def once(self, start, end):
        # Cache all dictionary accesses in local variables to speed up the loop
        darray = self.dataline.array
        larray = self.lines[0].array
        smfactor = self.smoothfactor
        smfactor1 = 1.0 - smfactor

        # Let MovingAverageSimple produce the 1st value
        super(MovingAverageSmoothing, self).once(start, start + 1)
        prev = larray[start]

        for i in xrange(start + 1, end):
            larray[i] = prev = prev * smfactor1 + darray[i] * smfactor


class MovingAverageExponential(MovingAverageSmoothing):
    plotname = 'EMA'

    def __init__(self):
        self.smoothfactor = 2.0 / (1.0 + self.fperiod)


class MovingAverageSmoothed(MovingAverageSmoothing):
    plotname = 'SMA'

    def __init__(self):
        self.smoothfactor = 1.0 / self.fperiod


class MASmoothedNAN(MovingAverageSmoothed):
    plotname = 'SMA_NAN'

    NAN = float('nan')

    def __init__(self):
        self.tofill = self.params.period - 1

    def prenext(self):
        value = self.dataline[0]

        if value == value: # value is not NAN
            super(MASmoothedNAN, self).prenext()
            self.tofill -= 1

    def next(self):
        value = self.dataline[0]
        lastout = self.lines[0][-1]

        if value != value: # value is NAN
            self.lines[0][0] = lastout
            return

        if lastout == lastout: # last output is NOT NAN
            super(MASmoothedNAN, self).next()

        else: # lastouput still NAN
            if not self.tofill:
                self.nextstart() # buffer will be full - kickstart
            else:
                self.prenext() # buffer to be filled - still in prenext phase

    def preonce(self, start, end):
        for i in xrange(start, end):
            value = self.dataline.array[i]

            if value == value: # value is not NAN
                self.dq.append(value)
                self.tofill -= 1

    def once(self, start, end):
        # Cache all dictionary accesses in local variables to speed up the loop
        darray = self.dataline.array
        larray = self.lines[0].array
        smfactor = self.smoothfactor
        smfactor1 = 1.0 - smfactor
        tofill = self.tofill

        lout1 = larray[start - 1]
        for i in xrange(start, end):
            data = darray[i]

            if data != data: # Input data is NAN ... repeat line output
                larray[i] = lout1

            elif lout1 == lout1: # line output was NOT NAN ... calc new output
                # produce a value
                larray[i] = lout1 = lout1 * smfactor1 + darray[i] * smfactor

            else: # lastouput still NAN
                if not tofill:
                    self.dq.append(darray[i])
                    larray[i] = lout1 = math.fsum(self.dq) / self.fperiod
                else:
                    self.dq.append(darray[i])
                    tofill -= 1


class MAEnum(object):
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
