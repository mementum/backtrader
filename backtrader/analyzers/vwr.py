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

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase
from . import Returns
from ..mathsupport import standarddev


class VWR(TimeFrameAnalyzerBase):
    '''计算 VWR（Variability-Weighted Return）的 analyzer。

    VWR 可以理解为使用 Log Returns 的改进型 SharpeRatio。

    Alias:

      - VariabilityWeightedReturn

    参考:

      - https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

    Args:
        timeframe: 统计使用的 timeframe，默认 ``None``。如果为 ``None``，
            报告整个 backtest period 的完整 return。传入
            ``TimeFrame.NoTimeFrame`` 可在不受时间约束的情况下考虑整个
            dataset。
        compression: timeframe 压缩倍数，默认 ``None``。仅用于日内
            timeframe。如果为 ``None``，使用系统中第 1 个 data 的
            compression。
        tann: 年化（normalization）平均 return 使用的 period 数量，默认
            ``None``。如果为 ``None``，会使用标准值:
            days=252、weeks=52、months=12、years=1。
        tau (float): 计算使用的 factor，默认 ``0.20``。
        sdev_max (float): 最大 standard deviation，默认 ``2.0``。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回包含 ``vwr`` key 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(VWR, _name='vwr')
    '''

    params = (
        ('tann', None),
        ('tau', 0.20),
        ('sdev_max', 2.0),
        ('fund', None),
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def __init__(self):
        # 子 log return analyzer
        self._returns = Returns(timeframe=self.p.timeframe,
                                compression=self.p.compression,
                                tann=self.p.tann)

    def start(self):
        super(VWR, self).start()
        # 为 [-1] 操作添加初始占位
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        if not self._fundmode:
            self._pis = [self.strategy.broker.getvalue()]  # 保留初始 value
        else:
            self._pis = [self.strategy.broker.fundvalue]  # 保留初始 value

        self._pns = [None]  # 保留最终 price/value

    def stop(self):
        super(VWR, self).stop()
        # 检查最后一次 dt_over 之后是否没有看到 value
        # 如果是，则会多出一个错位的 pi 和一个 None pn，需要清理
        if self._pns[-1] is None:
            self._pis.pop()
            self._pns.pop()

        # 从子 analyzer 获取结果
        rs = self._returns.get_analysis()
        ravg = rs['ravg']
        rnorm100 = rs['rnorm100']

        # 让 enumerate 中的 n 从 1 开始（表示 period 数量而不是 index）
        # 跳过用于同步的初始占位
        dts = []
        for n, pipn in enumerate(zip(self._pis, self._pns), 1):
            pi, pn = pipn

            dt = pn / (pi * math.exp(ravg * n)) - 1.0
            dts.append(dt)

        sdev_p = standarddev(dts, bessel=True)

        vwr = rnorm100 * (1.0 - pow(sdev_p / self.p.sdev_max, self.p.tau))
        self.rets['vwr'] = vwr

    def notify_fund(self, cash, value, fundvalue, shares):
        if not self._fundmode:
            self._pns[-1] = value  # 标注当前 period 最后看到的 pn
        else:
            self._pns[-1] = fundvalue  # 标注当前 period 的最后 pn

    def _on_dt_over(self):
        self._pis.append(self._pns[-1])  # 上一个 pn 是下一个 period 的 pi
        self._pns.append(None)  # [-1] 操作用占位


VariabilityWeightedReturn = VWR
