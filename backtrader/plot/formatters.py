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


import matplotlib.ticker as mplticker


class MyVolFormatter(mplticker.Formatter):
    Suffixes = ['', 'K', 'M', 'G', 'T', 'P']

    def __init__(self, volmax):
        self.volmax = volmax
        magnitude = 0
        self.divisor = 1.0
        while abs(volmax / self.divisor) >= 1000:
            magnitude += 1
            self.divisor *= 1000.0

        self.suffix = self.Suffixes[magnitude]

    def __call__(self, y, pos=0):
        '''Return the label for time x at position pos'''

        if y > self.volmax * 1.20:
            return ''

        y = int(y / self.divisor)
        return '%d%s' % (y, self.suffix)


class MyDateFormatter(mplticker.Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        '''Return the label for time x at position pos'''
        ind = int(round(x))
        if ind >= self.lendates or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)


class MyDateFormatter2(mplticker.Formatter):
    def __init__(self, dates, fmt='%b-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        '''Return the label for time x at position pos'''
        ind = int(round(x))
        if ind >= self.lendates or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)
