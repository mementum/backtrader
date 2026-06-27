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


class EnvelopeMixIn(object):
    '''
    Envelope 的 MixIn 基类，用于与另一个 indicator 组合，为其主 line 创建上下轨。
    上下轨与输入主 line 相差给定百分比 ``perc``。

    用法:

      - Class XXXEnvelope(XXX, EnvelopeMixIn)

    Formula:
      - 'line' (inherited from XXX))
      - top = 'line' * (1 + perc)
      - bot = 'line' * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes
    '''
    lines = ('top', 'bot',)
    params = (('perc', 2.5),)
    plotlines = dict(top=dict(_samecolor=True), bot=dict(_samecolor=True),)

    def __init__(self):
        # Mix-in 直接来自 object，并不一定需要 super
        # super(EnvelopeMixIn, self).__init__()
        perc = self.p.perc / 100.0

        self.lines.top = self.lines[0] * (1.0 + perc)
        self.lines.bot = self.lines[0] * (1.0 - perc)

        super(EnvelopeMixIn, self).__init__()


class _EnvelopeBase(Indicator):
    '''Envelope 的基类，用于保留源 data 并与上下轨一起绘图。'''
    lines = ('src',)

    # 将 envelope line 与传入源一起绘制
    plotinfo = dict(subplot=False)

    # 不重复绘制 data line
    plotlines = dict(src=dict(_plotskip=True))

    def __init__(self):
        self.lines.src = self.data
        super(_EnvelopeBase, self).__init__()


class Envelope(_EnvelopeBase, EnvelopeMixIn):
    '''
    按给定百分比在源 data 上下创建 envelope band。

    Args:
        perc: 上下轨相对源 data 的百分比距离。

    Returns:
        Envelope: 输出 ``src``、``top`` 与 ``bot`` line 的 indicator。

    Formula:
      - src = datasource
      - top = src * (1 + perc)
      - bot = src * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Envelope, perc=2.5)
    '''


# 自动创建 Moving Average Envelope 类

for movav in MovingAverage._movavs[1:]:
    _newclsdoc = '''
    %s 及其按 ``perc`` 分离的 envelope band。

    Formula:
      - %s (from %s)
      - top = %s * (1 + perc)
      - bot = %s * (1 - perc)

    See also:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_average_envelopes
    '''
    # 跳过 alias，它们会自动创建
    if getattr(movav, 'aliased', ''):
        continue

    movname = movav.__name__
    linename = movav.lines._getlinealias(0)
    newclsname = movname + 'Envelope'

    newaliases = []
    for alias in getattr(movav, 'alias', []):
        for suffix in ['Envelope']:
            newaliases.append(alias + suffix)

    newclsdoc = _newclsdoc % (movname, linename, movname, linename, linename)

    newclsdct = {'__doc__': newclsdoc,
                 '__module__': EnvelopeMixIn.__module__,
                 '_notregister': True,
                 'alias': newaliases}
    newcls = type(str(newclsname), (movav, EnvelopeMixIn), newclsdct)
    module = sys.modules[EnvelopeMixIn.__module__]
    setattr(module, newclsname, newcls)
