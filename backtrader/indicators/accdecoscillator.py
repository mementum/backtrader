#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
from . import MovAv, AwesomeOscillator


__all__ = ['AccelerationDecelerationOscillator', 'AccDeOsc']


class AccelerationDecelerationOscillator(bt.Indicator):
    '''
    Acceleration/Deceleration Technical Indicator（AC）用于衡量当前驱动力的加速和
    减速。

    该指标会先于驱动力变化而改变方向，而驱动力又通常先于价格改变方向。

    Args:
        period: 对 AwesomeOscillator 做 SMA 的周期。
        movav: 使用的 Moving Average 类型。

    Returns:
        AccelerationDecelerationOscillator: 输出 ``accde`` line 的 indicator。

    Formula:
     - AcdDecOsc = AwesomeOscillator - SMA(AwesomeOscillator, period)

    See:
      - https://www.metatrader5.com/en/terminal/help/indicators/bw_indicators/ao
      - https://www.ifcmarkets.com/en/ntx-indicators/ntx-indicators-accelerator-decelerator-oscillator

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AccelerationDecelerationOscillator)
    '''
    alias = ('AccDeOsc',)
    lines = ('accde', )

    params = (
        ('period', 5),
        ('movav', MovAv.SMA),
    )

    plotlines = dict(accde=dict(_method='bar', alpha=0.50, width=1.0))

    def __init__(self):
        ao = AwesomeOscillator()
        self.l.accde = ao - self.p.movav(ao, period=self.p.period)
        super(AccelerationDecelerationOscillator, self).__init__()
