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

from backtrader import Indicator
from backtrader.indicators import MovAv


class Envelope(Indicator):
    '''Envelope

    It creates envelopes bands separated from the source data by a given
    percentage

    Formula:
      - mid = datasource
      - top = datasource * (1 + perc)
      - bot = datasource * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - mid
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
    '''

    lines = ('mid', 'top', 'bot',)
    params = (('perc', 2.5),)

    def __init__(self):
        perc = self.p.perc / 100.0

        self._prepare()
        data = self._envsource()

        self.lines.mid = data
        self.lines.top = data * (1.0 + perc)
        self.lines.bot = data * (1.0 - perc)

    def _prepare(self):
        pass

    def _envsource(self):
        return self.data


class _MAEnvelope(Envelope):
    params = (('movav', MovAv.SMA), ('period', None),)
    plotinfo = dict(subplot=False)
    plotlines = dict(
        mid=dict(ls='--'),
        top=dict(_samecolor=True),
        bot=dict(_samecolor=True),)

    def _plotlabel(self):
        plabels = [self.p.period, self.p.perc]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def _prepare(self):
        self.p.period = self.p.period or self.p.movav.params.period

    def _envsource(self):
        return self.p.movav(self.data, period=self.p.period)


class SMAEnvelope(_MAEnvelope):
    '''SMAEnvelope

    SimpleMovingAverage and envelope band separated "perc" from it

    Formula:
      - mid = SimpleMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - mid
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
    '''
    pass


class EMAEnvelope(_MAEnvelope):
    '''EMAEnvelope

    ExponentialMovingAverage and envelope band separated "perc" from it

    Formula:
      - mid = ExponentialMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - mid
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
    '''
    params = (('movav', MovAv.EMA),)


class SMMAEnvelope(_MAEnvelope):
    '''SMMAEnvelope

    SmoothingMovingAverage and envelope band separated "perc" from it

    Formula:
      - mid = SmoothingMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - mid
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
    '''
    params = (('movav', MovAv.SMMA),)


class WMAEnvelope(_MAEnvelope):
    '''WMAEnvelope

    WeightedMovingAverage and envelope band separated "perc" from it

    Formula:
      - mid = WeightedMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - mid
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
    '''
    params = (('movav', MovAv.WMA),)


class KAMAEnvelope(_MAEnvelope):
    '''KAMAEnvelope

    AdaptiveMovingAverage and envelope band separated "perc" from it

    Formula:
      - mid = AdaptiveMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - mid
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
      - fast (2): period for the fast adaptive exponential factor
      - fast (30): period for the slow adaptive exponential factor
    '''
    params = (('movav', MovAv.KAMA), ('fast', None), ('slow', None),)

    def _plotlabel(self):
        plabels = [self.p.period, self.p.fast, self.p.slow, self.p.perc]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def _prepare(self):
        super(KAMAEnvelope)._prepare()
        self.p.fast = self.p.fast or self.p.movav.params.fast
        self.p.slow = self.p.slow or self.p.movav.params.slow

    def _envsource(self):
        return self.p.movav(self.data, period=self.p.period,
                            fast=self.p.fast, slow=self.p.slow)
