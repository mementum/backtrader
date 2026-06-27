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

from colorsys import rgb_to_hls as rgb2hls, hls_to_rgb as hls2rgb

import matplotlib.colors as mplcolors
import matplotlib.path as mplpath


def tag_box_style(x0, y0, width, height, mutation_size, mutation_aspect=1):
    """根据 box 的位置和尺寸返回包围它的 path。

    Args:
        x0: box 左下角 x 坐标。
        y0: box 左下角 y 坐标。
        width: box 宽度。
        height: box 高度。
        mutation_size: mutation 的参考尺度。
        mutation_aspect: mutation 的 aspect ratio。

    Returns:
        matplotlib.path.Path: 包围 box 的 path。
    """

    # 这里忽略 mutation_aspect；通常这是可接受的。
    mypad = 0.2
    pad = mutation_size * mypad

    # 加上 padding 后的 width 和 height。
    width, height = width + 2.*pad, height + 2.*pad,

    # padded box 的边界
    x0, y0 = x0-pad, y0-pad,
    x1, y1 = x0+width, y0 + height

    cp = [(x0, y0),
          (x1, y0), (x1, y1), (x0, y1),
          (x0-pad, (y0+y1)/2.), (x0, y0),
          (x0, y0)]

    com = [mplpath.Path.MOVETO,
           mplpath.Path.LINETO, mplpath.Path.LINETO, mplpath.Path.LINETO,
           mplpath.Path.LINETO, mplpath.Path.LINETO,
           mplpath.Path.CLOSEPOLY]

    path = mplpath.Path(cp, com)

    return path


def shade_color(color, percent):
    """调亮或调暗颜色。

    Args:
        color: 任意 Matplotlib 可接受的颜色值，例如 ``'red'``、``'slategrey'``、
            ``'#FFEE11'``、``(1, 0, 0)``。
        percent: 调亮或调暗的百分比；正数变亮，负数变暗。

    Returns:
        tuple: 转换后的 RGB float 值。
    """

    rgb = mplcolors.colorConverter.to_rgb(color)

    h, l, s = rgb2hls(*rgb)

    l *= 1 + float(percent)/100

    l = min(1, l)
    l = max(0, l)

    r, g, b = hls2rgb(h, l, s)

    return r, g, b
