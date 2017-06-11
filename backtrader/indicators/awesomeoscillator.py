#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Ssoftware Foundation, either version 3 of the License, or
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
from . import SMA

class AwesomeOscillator(bt.Indicator):
    '''
    Awesome Oscillator (AO) is a momentum indicator reflecting the precise
    changes in the market driving force which helps to identify the trend’s
    strength up to the points of formation and reversal.


    Formula:
     - MEDIAN PRICE = (HIGH+LOW)/2
     - AO = SMA(MEDIAN PRICE, 5)-SMA(MEDIAN PRICE, 34)

    See:
      - https://www.metatrader5.com/en/terminal/help/indicators/bw_indicators/awesome
      - https://www.ifcmarkets.com/en/ntx-indicators/awesome-oscillator

    '''
    alias = ('AO',)
    lines = ('ao',)

    plotlines = dict(ao=dict(_method='bar'))

    def __init__(self):
        median_price = (self.data.high + self.data.low) / 2
        sma1 = SMA(median_price, period=5)
        sma2 = SMA(median_price, period=34)
        self.l.ao = sma1 - sma2
