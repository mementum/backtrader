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

import sys


from . import Indicator, MovingAverage


class OscillatorMixIn(Indicator):
    '''
    Oscillator 的 MixIn 基类，用于与另一个 indicator 组合生成 oscillator。
    该 indicator 的主 line 会从另一个基类的主 line 中扣除。

    用法:

      - Class XXXOscillator(XXX, OscillatorMixIn)

    Formula:
      - XXX calculates lines[0]
      - osc = self.data - XXX.lines[0]
    '''
    plotlines = dict(_0=dict(_name='osc'))

    def _plotinit(self):
        try:
            lname = self.lines._getlinealias(0)
            self.plotlines._0._name = lname + '_osc'
        except AttributeError:
            pass

    def __init__(self):
        self.lines[0] = self.data - self.lines[0]
        super(OscillatorMixIn, self).__init__()


class Oscillator(Indicator):
    '''
    给定 data 围绕另一个 data 的 oscillation。

    Args:
        data: 单 data 模式下为带有原始 datas 的 Lines 对象；双 data 模式下为基准
            data。
        data1: 双 data 模式下用于计算 oscillation 的另一个 data。

    Returns:
        Oscillator: 输出 ``osc`` line 的 indicator。

    Datas:
      该 indicator 可接受 1 或 2 个 data 进行计算。

      - 如果提供 1 个 data，它必须是同时持有 ``datas`` 的复杂 "Lines" 对象
        （indicator）。例如：Moving Average。

        计算结果表示该 Moving Average 围绕其计算所用原始 data 的 oscillation。

      - 如果提供 2 个 data，则表示第 2 个 data 围绕第 1 个 data 的 oscillation。

    Formula:
      - 1 data -> osc = data.data - data
      - 2 datas -> osc = data0 - data1

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> from backtrader.indicators import SimpleMovingAverage
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(SimpleMovingAverage)
    >>> cerebro.addindicator(Oscillator)
    '''
    lines = ('osc',)

    # 提供默认值，后续可按需修改
    plotlines = dict(_0=dict(_name='osc'))

    def _plotinit(self):
        try:
            lname = self.dataosc._getlinealias(0)
            self.plotlines._0._name = lname + '_osc'
        except AttributeError:
            pass

    def __init__(self):
        super(Oscillator, self).__init__()

        if len(self.datas) > 1:
            datasrc = self.data
            self.dataosc = self.data1
        else:
            datasrc = self.data.data
            self.dataosc = self.data

        self.lines[0] = datasrc - self.dataosc


# 自动创建 Oscillating Lines

for movav in MovingAverage._movavs[1:]:
    _newclsdoc = '''
    %s 围绕其 data 的 oscillation。
    '''
    # 跳过 alias，它们会自动创建
    if getattr(movav, 'aliased', ''):
        continue

    movname = movav.__name__
    linename = movav.lines._getlinealias(0)
    newclsname = movname + 'Oscillator'

    newaliases = [movname + 'Osc']
    for alias in getattr(movav, 'alias', []):
        for suffix in ['Oscillator', 'Osc']:
            newaliases.append(alias + suffix)

    newclsdoc = _newclsdoc % movname
    newclsdct = {'__doc__': newclsdoc,
                 '__module__': OscillatorMixIn.__module__,
                 '_notregister': True,
                 'alias': newaliases}

    newcls = type(str(newclsname), (movav, OscillatorMixIn), newclsdct)
    module = sys.modules[OscillatorMixIn.__module__]
    setattr(module, newclsname, newcls)
