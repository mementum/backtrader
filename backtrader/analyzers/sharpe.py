#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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
import math
import operator

from backtrader.utils.py3 import map, itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import average, standarddev
from backtrader.analyzers import TimeReturn, AnnualReturn


class SharpeRatio(Analyzer):
    '''
    This analyzer calculates the SharpeRatio of a strategy using a risk free
    asset which is simply an interest rate

    See also:

      - https://en.wikipedia.org/wiki/Sharpe_ratio

    Params:

      - timeframe: (default: TimeFrame.Years)

      - compression (default: 1)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

      - riskfreerate: (default: 0.01 -> 1%)

        Expressed in annual terms (see ``convertrate`` below)

      - convertrate (default: True)

        Convert the ``riskfreerate`` from annual to monthly, weekly or daily
        rate. Sub-day conversions are not supported

      - daysfactor (default: 256)

        On a conversion of annual to daily rate use the value as the number of
        trading days in a year. Unlike months (12) and weeks (52) this can be
        adjusted

      - legacyannual (default: False)

        Use the 'AnnualReturn' return analyzer, which as the name implies only
        works on years

    Methods:

      - get_analysis

        Returns a dictionary with key "sharperatio" holding the ratio
    '''
    params = (
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
        ('riskfreerate', 0.01),
        ('convertrate', True),
        ('daysfactor', 256),
        ('legacyannual', False),
    )

    RATEFACTORS = {
        TimeFrame.Weeks: 52,
        TimeFrame.Months: 12,
        TimeFrame.Years: 1,
    }

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
            rate = self.p.riskfreerate
            if self.p.convertrate:
                factor = None
                if self.p.timeframe in self.RATEFACTORS:
                    # rate provided on an annual basis ... downgrade it
                    factor = self.RATEFACTORS[self.p.timeframe]
                elif self.p.timeframe == TimeFrame.Days:
                    factor = self.p.daysfactor

                if factor is not None:
                    rate = math.pow(1.0 + rate, 1.0 / factor) - 1.0

            returns = list(itervalues(self.timereturn.get_analysis()))
            retfree = itertools.repeat(rate)

            ret_free = map(operator.sub, returns, retfree)
            ret_free_avg = average(list(ret_free))
            retdev = standarddev(returns)

            self.ratio = ret_free_avg / retdev

    def get_analysis(self):
        return dict(sharperatio=self.ratio)
