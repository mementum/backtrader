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


__all__ = ['PercentChange', 'PctChange']


class PercentChange(Indicator):
    '''
    计算当前值相对 ``period`` 个 bar 前的 percentage change。

    Args:
        period: 回看周期。

    Returns:
        PercentChange: 输出 ``pctchange`` line 的 indicator。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PercentChange, period=30)
    '''
    alias = ('PctChange',)
    lines = ('pctchange',)

    # 更适合绘图显示的名称
    plotlines = dict(pctchange=dict(_name='%change'))

    # 使用与 Moving Averages 统一的 period 参数名
    params = (('period', 30),)

    def __init__(self):
        self.lines.pctchange = self.data / self.data(-self.p.period) - 1.0
        super(PercentChange, self).__init__()
