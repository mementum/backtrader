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

from . import PeriodN


__all__ = ['ParabolicSAR', 'PSAR']


class _SarStatus(object):
    '''ParabolicSAR 的内部状态对象，用于保存当前/上一轮趋势状态。'''
    sar = None
    tr = None
    af = 0.0
    ep = 0.0

    def __str__(self):
        txt = []
        txt.append('sar: {}'.format(self.sar))
        txt.append('tr: {}'.format(self.tr))
        txt.append('af: {}'.format(self.af))
        txt.append('ep: {}'.format(self.ep))
        return '\n'.join(txt)


class ParabolicSAR(PeriodN):
    '''
    J. Welles Wilder, Jr. 于 1978 年在 *"New Concepts in Technical Trading
    Systems"* 中定义的 Parabolic SAR。

    SAR 表示 *Stop and Reverse*，该 indicator 设计为入场与反转信号。

    原书未明确说明如何选择第一个信号以及 bar 增减的处理细节。

    Args:
        period: 开始显示数值前的最小周期。
        af: acceleration factor 初始增量。
        afmax: acceleration factor 最大值。

    Returns:
        ParabolicSAR: 输出 ``psar`` line 的 indicator。

    See:
      - https://en.wikipedia.org/wiki/Parabolic_SAR
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:parabolic_sar

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ParabolicSAR)
    '''
    alias = ('PSAR',)
    lines = ('psar',)
    params = (
        ('period', 2),  # 何时开始显示数值
        ('af', 0.02),
        ('afmax', 0.20),
    )

    plotinfo = dict(subplot=False)
    plotlines = dict(
        psar=dict(
            marker='.', markersize=4.0, color='black', fillstyle='full', ls=''
        ),
    )

    def prenext(self):
        if len(self) == 1:
            self._status = []  # 空状态
            return  # 数据不足，无法计算

        elif len(self) == 2:
            self.nextstart()  # 启动计算
        else:
            self.next()  # 常规计算

        self.lines.psar[0] = float('NaN')  # 仍处于 prenext，暂不返回有效值

    def nextstart(self):
        if self._status:  # 已经计算出部分状态
            self.next()  # 委托给 next
            return

        # 准备状态数组，分别保存当前长度和上一长度的状态
        self._status = [_SarStatus(), _SarStatus()]

        # 先观察第 2 天 close 的涨跌来获得 entry 信号，并按“上一趋势”的形态设置值。
        # 其中 sar 会在 next 中立即失效，随后反转并根据 close 计算出的实际涨跌设置趋势。
        # 4 个状态变量放入状态持有对象。
        plenidx = (len(self) - 1) % 2  # 上一长度索引（0 或 1）
        status = self._status[plenidx]

        # 计算上一长度的状态
        status.sar = (self.data.high[0] + self.data.low[0]) / 2.0

        status.af = self.p.af
        if self.data.close[0] >= self.data.close[-1]:  # 上升趋势
            status.tr = not True  # 反转后为上升趋势
            status.ep = self.data.low[-1]  # 来自上一趋势的 ep
        else:
            status.tr = not False  # 反转后为下降趋势
            status.ep = self.data.high[-1]  # 来自上一趋势的 ep

        # 带着伪造的上一趋势和即将失效的 sar 进入 next，完成正式计算
        self.next()

    def next(self):
        hi = self.data.high[0]
        lo = self.data.low[0]

        plenidx = (len(self) - 1) % 2  # 上一长度索引（0 或 1）
        status = self._status[plenidx]  # 使用上一状态进行计算

        tr = status.tr
        sar = status.sar

        # 检查 sar 是否穿透价格以切换趋势
        if (tr and sar >= lo) or (not tr and sar <= hi):
            tr = not tr  # 反转趋势
            sar = status.ep  # 新 sar 使用上一 SIP（Significant price）
            ep = hi if tr else lo  # 选择新的 SIP / Extreme Price
            af = self.p.af  # 重置 acceleration factor

        else:  # 使用预计算值
            ep = status.ep
            af = status.af

        # 更新今日 sar 值
        self.lines.psar[0] = sar

        # 按需更新 ep 和 af
        if tr:  # 多头趋势
            if hi > ep:
                ep = hi
                af = min(af + self.p.af, self.p.afmax)

        else:  # 下降趋势
            if lo < ep:
                ep = lo
                af = min(af + self.p.af, self.p.afmax)

        sar = sar + af * (ep - sar)  # 计算明日 sar

        # 确保 sar 不进入 high/low 区间
        if tr:  # 多头趋势
            lo1 = self.data.low[-1]
            if sar > lo or sar > lo1:
                sar = min(lo, lo1)  # sar 不高于最近 2 个 low -> 取较低值
        else:
            hi1 = self.data.high[-1]
            if sar < hi or sar < hi1:
                sar = max(hi, hi1)  # sar 不低于最近 2 个 high -> 取较高值

        # 新状态已经计算完成，保存在当前长度中，供下一次长度推进时使用
        newstatus = self._status[not plenidx]
        newstatus.tr = tr
        newstatus.sar = sar
        newstatus.ep = ep
        newstatus.af = af
