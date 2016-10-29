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

import backtrader as bt
from . import SMA, ROC100


class KnowSureThing(bt.Indicator):
    '''
    It is a "summed" momentum indicator. Developed by Martin Pring and
    published in 1992 in Stocks & Commodities.

    Formula:
      - rcma1 = MovAv(roc100(rp1), period)
      - rcma2 = MovAv(roc100(rp2), period)
      - rcma3 = MovAv(roc100(rp3), period)
      - rcma4 = MovAv(roc100(rp4), period)

      - kst = 1.0 * rcma1 + 2.0 * rcma2 + 3.0 * rcma3 + 4.0 * rcma4
      - signal = MovAv(kst, speriod)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:know_sure_thing_kst

    Params

      - ``period``: for the MovingAverage on the ROCs
      - ``rp1``, ``rp2``, ``rp3``, ``rp4``: for the ROCs
      - ``speriod``: for the MovingAverage for the signal line
      - ``rfactors``: list of factors to apply to the different MovAv(ROCs)
      - ``_movav`` and ``_movavs``, allows to change the Moving Average type
        applied for the calculation of kst and signal

    '''
    alias = ('KST',)
    lines = ('kst', 'signal',)
    params = (
        ('period', 10), ('speriod', 9),
        ('rp1', 10), ('rp2', 15), ('rp3', 20), ('rp4', 30),
        ('rfactors', [1.0, 2.0, 3.0, 4.0]),
        ('_movav', SMA),
        ('_movavsig', SMA),
    )

    plotinfo = dict(plothlines=[0.0])

    def __init__(self):
        rcma1 = self.p._movav(ROC100(period=self.p.rp1), period=self.p.period)
        rcma2 = self.p._movav(ROC100(period=self.p.rp2), period=self.p.period)
        rcma3 = self.p._movav(ROC100(period=self.p.rp3), period=self.p.period)
        rcma4 = self.p._movav(ROC100(period=self.p.rp4), period=self.p.period)
        self.l.kst = sum([rfi * rci for rfi, rci in
                          zip(self.p.rfactors, [rcma1, rcma2, rcma3, rcma4])])

        self.l.signal = self.p._movavsig(self.l.kst, period=self.p.speriod)
        super(KnowSureThing, self).__init__()
