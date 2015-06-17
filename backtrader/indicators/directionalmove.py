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

from backtrader import Indicator, And, If
from backtrader.indicators import MovAv, ATR


class UpMove(Indicator):
    '''UpMove

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"* as part of the Directional Move System to
    calculate Directional Indicators.

    Positive if the given data has moved higher than the previous day

    Formula:
      - upmove = data - data(-1)

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Lines:
      - upmove

    Params:
      (None)
    '''
    lines = ('upmove',)

    def __init__(self):
        self.lines.upmove = self.data - self.data(-1)


class DownMove(Indicator):
    '''DownMove

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"* as part of the Directional Move System to
    calculate Directional Indicators.

    Positive if the given data has moved lower than the previous day

    Formula:
      - downmove = data(-1) - data

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Lines:
      - downmove

    Params:
      (None)
    '''
    lines = ('downmove',)

    def __init__(self):
        self.lines.downmove = self.data(-1) - self.data


class _DirectionalIndicator(Indicator):
    '''_DirectionalIndicator

    This class serves as the root base class for all "Directional Movement
    System" related indicators, given that the calculations are first common
    and then derived from the common calculations.

    It can calculate the +DI and -DI values (using kwargs as the hint as to
    what to calculate) but doesn't assign them to lines. This is left for
    sublcases of this class.
    '''
    params = (('period', 14), ('movav', MovAv.Smoothed))

    plotlines = dict(plusDI=dict(_name='+DI'), minusDI=dict(_name='-DI'))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self, _plus=True, _minus=True):
        atr = ATR(self.data, period=self.p.period, movav=self.p.movav)

        upmove = self.data.high - self.data.high(-1)
        downmove = self.data.low(-1) - self.data.low

        if _plus:
            plus = And(upmove > downmove, upmove > 0.0)
            plusDM = If(plus, upmove, 0.0)
            plusDMav = self.p.movav(plusDM, period=self.p.period)

            self.DIplus = 100.0 * plusDMav / atr

        if _minus:
            minus = And(downmove > upmove, downmove > 0.0)
            minusDM = If(minus, downmove, 0.0)
            minusDMav = self.p.movav(minusDM, period=self.p.period)

            self.DIminus = 100.0 * minusDMav / atr


class DirectionalIndicator(_DirectionalIndicator):
    '''DirectionalIndicator (alias DI)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength

    This indicator shows +DI, -DI:
      - Use PlusDirectionalIndicator (PlusDI) to get +DI
      - Use MinusDirectionalIndicator (MinusDI) to get -DI
      - Use AverageDirectionalIndex (ADX) to get ADX
      - Use AverageDirectionalIndexRating (ADXR) to get ADX, ADXR
      - Use DirectionalMovementIndex (DMI) to get ADX, +DI, -DI
      - Use DirectionalMovement (DM) to get ADX, ADXR, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - plusDI
      - minusDI

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    lines = ('plusDI', 'minusDI',)

    def __init__(self):
        if not hasattr(self, 'DIplus'):
            # Avoid recalculation in multiple inheritance below
            super(DirectionalIndicator, self).__init__()

        self.lines.plusDI = self.DIplus
        self.lines.minusDI = self.DIminus


class DI(DirectionalIndicator):
    pass  # alias


class PlusDirectionalIndicator(_DirectionalIndicator):
    '''PlusDirectionalIndicator (alias PlusDI)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength

    This indicator shows +DI:
      - Use MinusDirectionalIndicator (MinusDI) to get -DI
      - Use Directional Indicator (DI) to get +DI, -DI
      - Use AverageDirectionalIndex (ADX) to get ADX
      - Use AverageDirectionalIndexRating (ADXR) to get ADX, ADXR
      - Use DirectionalMovementIndex (DMI) to get ADX, +DI, -DI
      - Use DirectionalMovement (DM) to get ADX, ADXR, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - plusDI

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    lines = ('plusDI',)

    plotinfo = dict(plotname='+DirectionalIndicator')

    def __init__(self):
        super(PlusDirectionalIndicator, self).__init__(_minus=False)

        self.lines.plusDI = self.DIplus


class PlusDI(PlusDirectionalIndicator):
    plotinfo = dict(plotname='+DI')
    pass  # alias


class MinusDirectionalIndicator(_DirectionalIndicator):
    '''MinusDirectionalIndicator (alias MinusDI)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength

    This indicator shows -DI:
      - Use PlusDirectionalIndicator (PlusDI) to get +DI
      - Use Directional Indicator (DI) to get +DI, -DI
      - Use AverageDirectionalIndex (ADX) to get ADX
      - Use AverageDirectionalIndexRating (ADXR) to get ADX, ADXR
      - Use DirectionalMovementIndex (DMI) to get ADX, +DI, -DI
      - Use DirectionalMovement (DM) to get ADX, ADXR, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - -di = 100 * MovingAverage(-dm, period) / atr(period)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - minusDI

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    lines = ('minusDI',)

    plotinfo = dict(plotname='-DirectionalIndicator')

    def __init__(self):
        super(PlusDirectionalIndicator, self).__init__(_plus=False)

        self.lines.minusDI = self.DIminus


class MinusDI(MinusDirectionalIndicator):
    plotinfo = dict(plotname='-DI')
    pass  # alias


class AverageDirectionalMovementIndex(_DirectionalIndicator):
    '''AverageDirectionalMovementIndex (alias ADX)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength

    This indicator only shows ADX:
      - Use PlusDirectionalIndicator (PlusDI) to get +DI
      - Use MinusDirectionalIndicator (MinusDI) to get -DI
      - Use Directional Indicator (DI) to get +DI, -DI
      - Use AverageDirectionalIndexRating (ADXR) to get ADX, ADXR
      - Use DirectionalMovementIndex (DMI) to get ADX, +DI, -DI
      - Use DirectionalMovement (DM) to get ADX, ADXR, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - adx

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    lines = ('adx',)

    plotlines = dict(adx=dict(_name='ADX'))

    def __init__(self):
        super(AverageDirectionalMovementIndex, self).__init__()

        dx = abs(self.DIplus - self.DIminus) / (self.DIplus + self.DIminus)
        self.lines.adx = 100.0 * self.p.movav(dx, period=self.p.period)


class ADX(AverageDirectionalMovementIndex):
    pass  # alias


class AverageDirectionalMovementIndexRating(ADX):
    '''AverageDirectionalMovementIndexRating (alias ADXR)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength.

    ADXR is the average of ADX with a value period bars ago

    This indicator shows the ADX and ADXR:
      - Use PlusDirectionalIndicator (PlusDI) to get +DI
      - Use MinusDirectionalIndicator (MinusDI) to get -DI
      - Use Directional Indicator (DI) to get +DI, -DI
      - Use AverageDirectionalIndex (ADX) to get ADX
      - Use DirectionalMovementIndex (DMI) to get ADX, +DI, -DI
      - Use DirectionalMovement (DM) to get ADX, ADXR, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)
      - adxr = (adx + adx(-period)) / 2

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - adx
      - adxr

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    lines = ('adxr',)

    plotlines = dict(adxr=dict(_name='ADXR'))

    def __init__(self):
        super(AverageDirectionalMovementIndexRating, self).__init__()

        self.lines.adxr = (self.l.adx + self.l.adx(-self.p.period)) / 2.0


class ADXR(AverageDirectionalMovementIndexRating):
    pass  # alias


class DirectionalMovementIndex(ADX, DI):
    '''DirectionalMovementIndex (alias DMI)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength

    This indicator shows the ADX, +DI, -DI:
      - Use PlusDirectionalIndicator (PlusDI) to get +DI
      - Use MinusDirectionalIndicator (MinusDI) to get -DI
      - Use Directional Indicator (DI) to get +DI, -DI
      - Use AverageDirectionalIndex (ADX) to get ADX
      - Use AverageDirectionalIndexRating (ADXRating) to get ADX, ADXR
      - Use DirectionalMovement (DM) to get ADX, ADXR, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - adx
      - plusDI
      - minusDI

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    pass


class DMI(DirectionalMovementIndex):
    pass  # alias


class DirectionalMovement(ADXR, DI):
    '''DirectionalMovement (alias DM)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    Intended to measure trend strength

    This indicator shows ADX, ADXR, +DI, -DI.

      - Use PlusDirectionalIndicator (PlusDI) to get +DI
      - Use MinusDirectionalIndicator (MinusDI) to get -DI
      - Use Directional Indicator (DI) to get +DI, -DI
      - Use AverageDirectionalIndex (ADX) to get ADX
      - Use AverageDirectionalIndexRating (ADXR) to get ADX, ADXR
      - Use DirectionalMovementIndex (DMI) to get ADX, +DI, -DI

    Formula:
      - upmove = high - high(-1)
      - downmove = low(-1) - low
      - +dm = upmove if upmove > downmove and upmove > 0 else 0
      - -dm = downmove if downmove > upmove and downmove > 0 else 0
      - +di = 100 * MovingAverage(+dm, period) / atr(period)
      - -di = 100 * MovingAverage(-dm, period) / atr(period)
      - dx = 100 * abs(+di - -di) / (+di + -di)
      - adx = MovingAverage(dx, period)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - https://en.wikipedia.org/wiki/Average_directional_movement_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Lines:
      - adx
      - adxr
      - plusDI
      - minusDI

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
    '''
    pass


class DM(DirectionalMovement):
    pass  # alias
