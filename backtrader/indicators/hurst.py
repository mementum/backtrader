#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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

from . import PeriodN


__all__ = ['HurstExponent', 'Hurst']


class HurstExponent(PeriodN):
    '''
    References:

      - https://www.quantopian.com/posts/hurst-exponent
      - https://www.quantopian.com/posts/some-code-from-ernie-chans-new-book-implemented-in-python

   Interpretation of the results

      1. Geometric random walk (H=0.5)
      2. Mean-reverting series (H<0.5)
      3. Trending Series (H>0.5)
    '''
    frompackages = (
        ('numpy', ('asarray', 'log10', 'polyfit', 'sqrt', 'std', 'subtract')),
    )

    alias = ('Hurst',)
    lines = ('hurst',)
    params = (('period', 40),)

    def __init__(self):
        super(HurstExponent, self).__init__()
        # Prepare the lags array
        self.lags = asarray(range(2, self.p.period // 2))
        self.log10lags = log10(self.lags)

    def next(self):
        # Fetch the data
        ts = asarray(self.data.get(size=self.p.period))

        # Calculate the array of the variances of the lagged differences
        tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in self.lags]

        # Use a linear fit to estimate the Hurst Exponent
        poly = polyfit(self.log10lags, log10(tau), 1)

        # Return the Hurst exponent from the polyfit output
        self.lines.hurst[0] = poly[0] * 2.0
