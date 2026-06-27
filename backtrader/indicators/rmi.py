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

from . import RSI


class RelativeMomentumIndex(RSI):
    '''
    Roger Altman 开发的 Relative Momentum Index，并在 1993 年 2 月
    *Technical Analysis of Stocks & Commodities* 杂志文章中介绍。

    普通 RSI 统计 close 到 close 的涨跌日，Relative Momentum Index 则统计当前
    close 相对若干日前 close 的涨跌，因此结果会比 RSI 更平滑一些。

    用法与 RSI 类似，可观察 overbought/oversold 区域，也可用于 divergence
    与趋势分析。

    Args:
        period: RSI 平滑周期。
        lookback: 用来比较历史 close 的回看周期。

    Returns:
        RelativeMomentumIndex: 输出 ``rmi`` line 别名的 RSI 派生 indicator。

    See:
      - https://www.marketvolume.com/technicalanalysis/relativemomentumindex.asp
      - https://www.tradingview.com/script/UCm7fIvk-FREE-INDICATOR-Relative-Momentum-Index-RMI/
      - https://www.prorealcode.com/prorealtime-indicators/relative-momentum-index-rmi/

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(RelativeMomentumIndex, period=20, lookback=5)
    '''
    alias = ('RMI', )

    linealias = (('rsi', 'rmi',),)  # 为该类添加 rmi -> rsi 的 line 别名
    plotlines = dict(rsi=dict(_name='rmi'))  # 修改绘图时显示的 line 名称

    params = (
        ('period', 20),
        ('lookback', 5),
    )

    def _plotlabel(self):
        # 覆盖标签逻辑，始终显示 lookback，并将其放在 movav 之前
        plabels = [self.p.period]
        plabels += [self.p.lookback]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels
