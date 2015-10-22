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

import functools
import math

from .linebuffer import LineActions
from .utils.py3 import cmp, range


class Logic(LineActions):
    def __init__(self, *args):
        super(Logic, self).__init__()
        self.args = [self.arrayize(arg) for arg in args]


class DivByZero(Logic):
    '''This operation is a Lines object and fills it values by executing a
    division on the numerator / denominator arguments and avoiding a division
    by zero exception by checking the denominator

    Params:
      - a: numerator (numeric or iterable object ... mostly a Lines object)
      - b: denominator (numeric or iterable object ... mostly a Lines object)
      - zero (def: 0.0): value to apply if division by zero would be raised

    '''
    def __init__(self, a, b, zero=0.0):
        super(DivByZero, self).__init__(a, b)
        self.a = self.args[0]
        self.b = self.args[1]
        self.zero = zero

    def next(self):
        b = self.b[0]
        self[0] = self.a[0] / b if b else self.zero

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        zero = self.zero

        for i in range(start, end):
            b = srcb[i]
            dst[i] = srca[i] / b if b else zero


class Cmp(Logic):
    def __init__(self, a, b):
        super(Cmp, self).__init__(a, b)
        self.a = self.args[0]
        self.b = self.args[1]

    def next(self):
        self[0] = cmp(self.a[0], self.b[0])

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array

        for i in range(start, end):
            dst[i] = cmp(srca[i], srcb[i])


class If(Logic):
    def __init__(self, cond, a, b):
        super(If, self).__init__(a, b)
        self.a = self.args[0]
        self.b = self.args[1]
        self.cond = self.arrayize(cond)

    def next(self):
        self[0] = self.a[0] if self.cond[0] else self.b[0]

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        cond = self.cond.array

        for i in range(start, end):
            dst[i] = srca[i] if cond[i] else srcb[i]


class MultiLogic(Logic):
    def next(self):
        self[0] = self.flogic([arg[0] for arg in self.args])

    def once(self, start, end):
        # cache python dictionary lookups
        dst = self.array
        arrays = [arg.array for arg in self.args]
        flogic = self.flogic

        for i in range(start, end):
            dst[i] = flogic([arr[i] for arr in arrays])


class MultiLogicReduce(MultiLogic):
    def __init__(self, *args):
        super(MultiLogicReduce, self).__init__(*args)
        self.flogic = functools.partial(functools.reduce, self.flogic)


# The _xxxlogic functions are defined at module scope to make them
# pickable and therefore compatible with multiprocessing
def _andlogic(x, y):
    return bool(x and y)


class And(MultiLogicReduce):
    flogic = staticmethod(_andlogic)


def _orlogic(x, y):
    return bool(x or y)


class Or(MultiLogicReduce):
    flogic = staticmethod(_orlogic)


class Max(MultiLogic):
    flogic = max


class Min(MultiLogic):
    flogic = min


class Sum(MultiLogic):
    flogic = math.fsum
