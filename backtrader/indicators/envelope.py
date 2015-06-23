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


class _EnvelopeMixIn(object):
    lines = ('top', 'bot',)
    params = (('perc', 2.5),)
    plotlines = dict(top=dict(_samecolor=True), bot=dict(_samecolor=True),)

    def __init__(self):
        # Mix-in & directly from object -> does not necessarily need super
        # super(_EnvelopeMixIn, self).__init__()
        perc = self.p.perc / 100.0

        self.lines.top = self.line * (1.0 + perc)
        self.lines.bot = self.line * (1.0 - perc)

        super(_EnvelopeMixIn, self).__init__()


class SMAEnvelope(MovAv.SMA, _EnvelopeMixIn):
    '''SMAEnvelope

    SimpleMovingAverage and envelope band separated "perc" from it

    Formula:
      - ma = SimpleMovingAverage
      - top = ma * (1 + perc)
      - bot = ma * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - ma
      - top
      - bot

    Params:
      - period (30): period to apply to the moving average
      - perc (2.5): percentage to separate the envelope bands from the source
    '''
    pass


class EMAEnvelope(MovAv.EMA, _EnvelopeMixIn):
    '''EMAEnvelope

    ExponentialMovingAverage and envelope band separated "perc" from it

    Formula:
      - ma = ExponentialMovingAverage
      - top = ma * (1 + perc)
      - bot = ma * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - ema
      - top
      - bot

    Params:
      - period (30): period to apply to the moving average
      - perc (2.5): percentage to separate the envelope bands from the source
    '''
    pass


class SMMAEnvelope(MovAv.SMMA, _EnvelopeMixIn):
    '''SMMAEnvelope

    SmoothingMovingAverage and envelope band separated "perc" from it

    Formula:
      - ma = SmoothingMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - ma
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
    '''
    pass


class WMAEnvelope(MovAv.WMA, _EnvelopeMixIn):
    '''WMAEnvelope

    WeightedMovingAverage and envelope band separated "perc" from it

    Formula:
      - ma = WeightedMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - ma
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
    '''
    pass


class KAMAEnvelope(MovAv.KAMA, _EnvelopeMixIn):
    '''KAMAEnvelope

    AdaptiveMovingAverage and envelope band separated "perc" from it

    Formula:
      - ma = AdaptiveMovingAverage
      - top = mid * (1 + perc)
      - bot = mid * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    Lines:
      - ma
      - top
      - bot

    Params:
      - perc (2.5): percentage to separate the envelope bands from the source
      - period (30): period to apply to the moving average
      - fast (2): period for the fast adaptive exponential factor
      - fast (30): period for the slow adaptive exponential factor
    '''
    pass


class Envelope(Indicator, _EnvelopeMixIn):
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
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.lines.mid = self.data
        super(Envelope, self).__init__()
