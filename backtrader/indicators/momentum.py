#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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

from . import Indicator


class Momentum(Indicator):
    '''
    通过计算当前价格与指定周期前价格的差值，衡量价格变化。

    Args:
        period: 回看周期。

    Returns:
        Momentum: 输出 ``momentum`` line 的 indicator。

    Formula:
      - momentum = data - data_period

    See:
      - http://en.wikipedia.org/wiki/Momentum_(technical_analysis)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Momentum, period=12)
    '''
    lines = ('momentum',)
    params = (('period', 12),)
    plotinfo = dict(plothlines=[0.0])

    def __init__(self):
        self.l.momentum = self.data - self.data(-self.p.period)
        super(Momentum, self).__init__()


class MomentumOscillator(Indicator):
    '''
    衡量指定周期内价格变化的比率。

    Args:
        period: 回看周期。
        band: 绘图时的参考线。

    Returns:
        MomentumOscillator: 输出 ``momosc`` line 的 indicator。

    Formula:
      - mosc = 100 * (data / data_period)

    See:
      - http://ta.mql4.com/indicators/oscillators/momentum

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(MomentumOscillator, period=12)
    '''
    alias = ('MomentumOsc',)

    # 命名输出 line
    lines = ('momosc',)

    # 可接受参数及默认值
    params = (('period', 12),
              ('band', 100.0))

    def _plotlabel(self):
        plabels = [self.p.period]
        return plabels

    def _plotinit(self):
        self.plotinfo.plothlines = [self.p.band]

    def __init__(self):
        self.l.momosc = 100.0 * (self.data / self.data(-self.p.period))
        super(MomentumOscillator, self).__init__()


class RateOfChange(Indicator):
    '''
    衡量指定周期内价格变化的相对比率。

    Args:
        period: 回看周期。

    Returns:
        RateOfChange: 输出 ``roc`` line 的 indicator。

    Formula:
      - roc = (data - data_period) / data_period

    See:
      - http://en.wikipedia.org/wiki/Momentum_(technical_analysis)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RateOfChange, period=12)
    '''
    alias = ('ROC',)

    # 命名输出 line
    lines = ('roc',)

    # 可接受参数及默认值
    params = (('period', 12),)

    def __init__(self):
        dperiod = self.data(-self.p.period)
        self.l.roc = (self.data - dperiod) / dperiod
        super(RateOfChange, self).__init__()


class RateOfChange100(Indicator):
    '''
    以 100 为基准衡量指定周期内价格变化的相对比率。

    例如 stockcharts 中的 ROC 即采用这种定义。

    Args:
        period: 回看周期。

    Returns:
        RateOfChange100: 输出 ``roc100`` line 的 indicator。

    Formula:
      - roc = 100 * (data - data_period) / data_period

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:rate_of_change_roc_and_momentum

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RateOfChange100, period=12)
    '''
    alias = ('ROC100',)

    # 命名输出 line
    lines = ('roc100',)

    # 可接受参数及默认值
    params = (('period', 12),)

    def __init__(self):
        self.l.roc100 = 100.0 * ROC(self.data, period=self.p.period)
        super(RateOfChange100, self).__init__()
