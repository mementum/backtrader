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

import itertools
import operator

from backtrader.utils.py3 import map, itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import average, standarddev
from backtrader.analyzers import TimeReturn, AnnualReturn


class SharpeRatio(Analyzer):
    '''
    This analyzer calculates the SharpRatio of a strategy using a risk free
    asset which is simply an interest rate

    Params:

      - riskfreerate: (default: 0.01 -> 1%)

    Member Attributes:

      - ``anret``: list of annual returns used for the final calculation

    **get_analysis**:

      - Returns a dictionary with key "sharperatio" holding the ratio
    '''
    params = (
        ('riskfreerate', 0.01),
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
        ('legacyannual', False),
    )

    def __init__(self):
        super(SharpeRatio, self).__init__()
        if self.p.legacyannual:
            self.anret = AnnualReturn()
        else:
            self.timereturn = TimeReturn(
                timeframe=self.p.timeframe,
                compression=self.p.compression)

    def stop(self):
        if self.p.legacyannual:
            retfree = [self.p.riskfreerate] * len(self.anret.rets)
            retavg = average(list(map(operator.sub, self.anret.rets, retfree)))
            retdev = standarddev(self.anret.rets)

            self.ratio = retavg / retdev
        else:
            returns = list(itervalues(self.timereturn.get_analysis()))
            retfree = itertools.repeat(self.p.riskfreerate)

            ret_free = map(operator.sub, returns, retfree)
            ret_free_avg = average(list(ret_free))
            retdev = standarddev(returns)

            self.ratio = ret_free_avg / retdev

    def get_analysis(self):
        return dict(sharperatio=self.ratio)
