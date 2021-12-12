#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
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

import math

from numpy import sqrt
from backtrader.functions import MultiLogicReduce

from backtrader.utils.py3 import itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import average, standarddev
from backtrader.analyzers import TimeReturn, AnnualReturn


class Volatility(Analyzer):
    '''This analyzer calculates the SharpeRatio of a strategy using a risk free
    asset which is simply an interest rate

    See also:

      - https://en.wikipedia.org/wiki/Sharpe_ratio

    Params:

      - ``timeframe``: (default: ``TimeFrame.Years``)

      - ``compression`` (default: ``1``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

      - ``riskfreerate`` (default: 0.01 -> 1%)

        Expressed in annual terms (see ``convertrate`` below)

      - ``convertrate`` (default: ``True``)

        Convert the ``riskfreerate`` from annual to monthly, weekly or daily
        rate. Sub-day conversions are not supported

      - ``factor`` (default: ``None``)

        If ``None``, the conversion factor for the riskfree rate from *annual*
        to the chosen timeframe will be chosen from a predefined table

          Days: 252, Weeks: 52, Months: 12, Years: 1

        Else the specified value will be used

      - ``annualize`` (default: ``False``)

        If ``convertrate`` is ``True``, the *SharpeRatio* will be delivered in
        the ``timeframe`` of choice.

        In most occasions the SharpeRatio is delivered in annualized form.
        Convert the ``riskfreerate`` from annual to monthly, weekly or daily
        rate. Sub-day conversions are not supported

      - ``stddev_sample`` (default: ``False``)

        If this is set to ``True`` the *standard deviation* will be calculated
        decreasing the denominator in the mean by ``1``. This is used when
        calculating the *standard deviation* if it's considered that not all
        samples are used for the calculation. This is known as the *Bessels'
        correction*

      - ``daysfactor`` (default: ``None``)

        Old naming for ``factor``. If set to anything else than ``None`` and
        the ``timeframe`` is ``TimeFrame.Days`` it will be assumed this is old
        code and the value will be used

      - ``legacyannual`` (default: ``False``)

        Use the ``AnnualReturn`` return analyzer, which as the name implies
        only works on years

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - get_analysis

        Returns a dictionary with key "sharperatio" holding the ratio

    '''
    params = (
        ('timeframe', TimeFrame.Days),
        ('compression', 1),
        ('riskfreerate', 0.01),
        ('factor', None),
        ('convertrate', True),
        ('annualize', False),
        ('stddev_sample', False),

        # old behavior
        ('daysfactor', None),
        ('legacyannual', False),
        ('fund', None),
    )

    RATEFACTORS = {
        TimeFrame.Days: 252,
        TimeFrame.Weeks: 52,
        TimeFrame.Months: 12,
        TimeFrame.Years: 1,
    }

    def __init__(self):
        if self.p.legacyannual:
            self.anret = AnnualReturn()
        else:
            self.timereturn = TimeReturn(
                timeframe=self.p.timeframe,
                compression=self.p.compression,
                fund=self.p.fund)

    def stop(self):
        super(Volatility, self).stop()
        if self.p.legacyannual:
            rate = self.p.riskfreerate
            retavg = average([r - rate for r in self.anret.rets])
            retdev = standarddev(self.anret.rets)

            self.ratio = retavg / retdev
        else:
            # Get the returns from the subanalyzer
            returns = list(itervalues(self.timereturn.get_analysis()))
            retdev = standarddev(returns)
            volatility = retdev * sqrt(len(returns))

            

        self.rets['volatility'] = volatility


