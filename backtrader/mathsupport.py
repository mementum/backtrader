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

import math


def average(x, bessel=False):
    '''计算序列的平均值。

    Args:
      x: 支持 ``len`` 的 iterable。
      bessel: 是否使用 ``N - 1`` 作为分母，常用于 Bessel 校正。

    Returns:
      float: ``x`` 中元素的平均值。

    ---
    交互示例：
      >>> average([1, 2, 3])
      2.0
    '''
    return math.fsum(x) / (len(x) - bessel)


def variance(x, avgx=None):
    '''计算序列每个元素相对平均值的平方偏差。

    Args:
      x: 支持 ``len`` 的 iterable。
      avgx: 已预先计算好的平均值；默认 ``None`` 时内部调用 ``average``。

    Returns:
      list: ``x`` 中每个元素的平方偏差。

    ---
    交互示例：
      >>> variance([1, 2, 3])
      [1.0, 0.0, 1.0]
    '''
    if avgx is None:
        avgx = average(x)
    return [pow(y - avgx, 2.0) for y in x]


def standarddev(x, avgx=None, bessel=False):
    '''计算序列的标准差。

    Args:
      x: 支持 ``len`` 的 iterable。
      avgx: 已预先计算好的平均值；默认 ``None`` 时内部计算。
      bessel: 是否按 ``N - 1`` 作为分母应用 Bessel 校正。

    Returns:
      float: ``x`` 中元素的标准差。

    ---
    交互示例：
      >>> round(standarddev([1, 2, 3]), 6)
      0.816497
    '''
    return math.sqrt(average(variance(x, avgx), bessel=bessel))
