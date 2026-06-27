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

from ..utils.py3 import with_metaclass

from . import Indicator


class MovingAverage(object):
    '''MovingAverage（别名 MovAv）的占位基类，用于集中登记所有 Moving Average 类型。

    实例化 SimpleMovingAverage 可使用下列写法::

      sma = MovingAverage.Simple(self.data, period)

    也可以使用更短的别名::

      sma = MovAv.SMA(self.data, period)

    或使用完整的正向/反向命名:

      sma = MovAv.SimpleMovingAverage(self.data, period)

      sma = MovAv.MovingAverageSimple(self.data, period)

    '''
    _movavs = []

    @classmethod
    def register(cls, regcls):
        if getattr(regcls, '_notregister', False):
            return

        cls._movavs.append(regcls)

        clsname = regcls.__name__
        setattr(cls, clsname, regcls)

        clsalias = ''
        if clsname.endswith('MovingAverage'):
            clsalias = clsname.split('MovingAverage')[0]
        elif clsname.startswith('MovingAverage'):
            clsalias = clsname.split('MovingAverage')[1]

        if clsalias:
            setattr(cls, clsalias, regcls)


class MovAv(MovingAverage):
    pass  # 别名


class MetaMovAvBase(Indicator.__class__):
    # 将所有 MovingAverage 注册到占位类，以便自动创建 envelope 和 oscillator

    def __new__(meta, name, bases, dct):
        # 创建类
        cls = super(MetaMovAvBase, meta).__new__(meta, name, bases, dct)

        MovingAverage.register(cls)

        # 返回类
        return cls


class MovingAverageBase(with_metaclass(MetaMovAvBase, Indicator)):
    '''MovingAverage 的基类，用于统一 period 参数、绘图行为和自动登记逻辑。'''
    params = (('period', 30),)
    plotinfo = dict(subplot=False)
