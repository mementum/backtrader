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


tableau20 = [
    'steelblue',  # 0
    'lightsteelblue',  # 1
    'darkorange',  # 2
    'peachpuff',  # 3
    'green',  # 4
    'lightgreen',  # 5
    'crimson',  # 6
    'lightcoral',  # 7
    'mediumpurple',  # 8
    'thistle',  # 9
    'saddlebrown',  # 10
    'rosybrown',  # 11
    'orchid',  # 12
    'lightpink',  # 13
    'gray',  # 14
    'lightgray',  # 15
    'olive',  # 16
    'palegoldenrod',  # 17
    'mediumturquoise',  # 18
    'paleturquoise',  # 19
]

tableau10 = [
    'blue',  # 'steelblue',  # 0
    'darkorange',  # 1
    'green',  # 2
    'crimson',  # 3
    'mediumpurple',  # 4
    'saddlebrown',  # 5
    'orchid',  # 6
    'gray',  # 7
    'olive',  # 8
    'mediumturquoise',  # 9
]

tableau10_light = [
    'lightsteelblue',  # 0
    'peachpuff',  # 1
    'lightgreen',  # 2
    'lightcoral',  # 3
    'thistle',  # 4
    'rosybrown',  # 5
    'lightpink',  # 6
    'lightgray',  # 7
    'palegoldenrod',  # 8
    'paleturquoise',  # 9
]

tab10_index = [3, 0, 2, 1, 2, 4, 5, 6, 7, 8, 9]


class PlotScheme(object):
    '''绘图 scheme 配置容器，用于集中保存 plot 样式默认值。'''

    def __init__(self):
        # 控制 chart 是否紧凑排列，可只作用于 x 轴，也可同时作用于 y 轴（见 matplotlib）
        self.ytight = False

        # subchart 的 y-margin（top/bottom）。不会覆盖 plotinfo.plotymargin 选项
        self.yadjust = 0.0
        # 每条新 line 的 z-order 低于上一条。设为 False 时新 line 会绘制在上一条之上
        self.zdown = True
        # x 轴 date label 的旋转角度
        self.tickrotation = 15

        # major chart（datas）在整体 chart 中占多少“subparts”
        # 该值相对 subchart 总数成比例
        self.rowsmajor = 5

        # minor chart（indicators/observers）在整体 chart 中占多少“subparts”
        # 该值相对 subchart 总数成比例。
        # 它与 rowsmajor 一起定义 data chart 与 indicator/observer chart 的比例关系
        self.rowsminor = 1

        # subchart 之间的距离
        self.plotdist = 0.0

        # 是否在所有 chart 背景中显示 grid
        self.grid = True

        # OHLC bar 的默认 plotstyle（line -> line on close）
        # 其它选项：'bar' 和 'candle'
        self.style = 'line'

        # 'line on close' plot 的默认颜色
        self.loc = 'black'
        # bullish bar/candle 的默认颜色（0.75 -> gray intensity）
        self.barup = '0.75'
        # bearish bar/candle 的默认颜色
        self.bardown = 'red'
        # 应用于 bars/candles 的透明度级别（未使用）
        self.bartrans = 1.0

        # candlestick 是否填充，还是保持透明
        self.barupfill = True
        self.bardownfill = True

        # filled candlestick 的不透明度（1.0 opaque - 0.0 transparent）
        self.baralpha = 1.0

        # line 之间填充区域的 alpha blending（_fill_gt 和 _fill_lt）
        self.fillalpha = 0.20

        # 是否绘制 volume。注意：如果对应 data 没有 volume 值，即使这里为 True 也会跳过
        self.volume = True

        # volume 是叠加到 data 上，还是使用独立 subchart
        self.voloverlay = True
        # overlay 绘制时 volume 相对 data 的缩放
        self.volscaling = 0.33
        # 将 overlay volume 上推以提升可见性。如果 volume 与 data 重叠过多，需要实验调整
        self.volpushup = 0.00

        # bullish day volume 的默认颜色
        self.volup = '#aaaaaa'  # 0.66 of gray
        # bearish day volume 的默认颜色
        self.voldown = '#cc6073'  # (204, 96, 115)
        # overlay volume 时应用的透明度
        self.voltrans = 0.50

        # text label 的透明度（当前未使用）
        self.subtxttrans = 0.66
        # chart label 的默认 font size
        self.subtxtsize = 9

        # legend 的透明度（当前未使用）
        self.legendtrans = 0.25
        # indicator 是否在其 chart 中显示 legend
        self.legendind = True
        # indicator legend 的位置（见 matplotlib）
        self.legendindloc = 'upper left'

        # datafeed legend 的位置（见 matplotlib）
        self.legenddataloc = 'upper left'

        # 在 Object 名称后绘制 line 的最后一个 value
        self.linevalues = True

        # 在每条 line 末尾绘制带最后 value 的 tag
        self.valuetags = True

        # horizontal line 的默认颜色（见 plotinfo.plothlines）
        self.hlinescolor = '0.66'  # shade of gray
        # horizontal line 的默认样式
        self.hlinesstyle = '--'
        # horizontal line 的默认宽度
        self.hlineswidth = 1.0

        # 默认 color scheme: Tableau 10
        self.lcolors = tableau10

        # x 轴 tick 显示使用的 strftime format string
        self.fmt_x_ticks = '%Y-%m-%d %H:%M'

        # data point value 显示使用的 strftime format string
        self.fmt_x_data = None

    def color(self, idx):
        colidx = tab10_index[idx % len(tab10_index)]
        return self.lcolors[colidx]
