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

import backtrader as bt
from . import PeriodN


__all__ = ['OLS_Slope_InterceptN', 'OLS_TransformationN', 'OLS_BetaN',
           'CointN']


class OLS_Slope_InterceptN(PeriodN):
    '''
    使用 ``statsmodel.OLS``（Ordinary least squares）计算 data1 对 data0 的线性回归。

    依赖 ``pandas`` 与 ``statsmodels``。

    Args:
        period: 回归窗口长度。

    Returns:
        OLS_Slope_InterceptN: 输出 ``slope`` 与 ``intercept`` line 的 indicator。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(OLS_Slope_InterceptN, period=10)
    '''
    _mindatas = 2  # 确保至少传入 2 个 data feed

    packages = (
        ('pandas', 'pd'),
        ('statsmodels.api', 'sm'),
    )
    lines = ('slope', 'intercept',)
    params = (
        ('period', 10),
    )

    def next(self):
        p0 = pd.Series(self.data0.get(size=self.p.period))
        p1 = pd.Series(self.data1.get(size=self.p.period))
        p1 = sm.add_constant(p1)
        intercept, slope = sm.OLS(p0, p1).fit().params

        self.lines.slope[0] = slope
        self.lines.intercept[0] = intercept


class OLS_TransformationN(PeriodN):
    '''
    计算 data0 与 data1 的 ``zscore``。该类不直接使用外部包，但依赖使用
    ``pandas`` 与 ``statsmodels`` 的 ``OLS_Slope_InterceptN``。

    Args:
        period: 回归和统计窗口长度。

    Returns:
        OLS_TransformationN: 输出 ``spread``、``spread_mean``、``spread_std``
        与 ``zscore`` line 的 indicator。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(OLS_TransformationN, period=10)
    '''
    _mindatas = 2  # 确保至少传入 2 个 data feed
    lines = ('spread', 'spread_mean', 'spread_std', 'zscore',)
    params = (('period', 10),)

    def __init__(self):
        slint = OLS_Slope_InterceptN(*self.datas)

        spread = self.data0 - (slint.slope * self.data1 + slint.intercept)
        self.l.spread = spread

        self.l.spread_mean = bt.ind.SMA(spread, period=self.p.period)
        self.l.spread_std = bt.ind.StdDev(spread, period=self.p.period)
        self.l.zscore = (spread - self.l.spread_mean) / self.l.spread_std


class OLS_BetaN(PeriodN):
    '''
    使用 ``pandas.ols`` 计算 data1 对 data0 的回归 beta。

    依赖 ``pandas``。

    Args:
        period: 回归窗口长度。

    Returns:
        OLS_BetaN: 输出 ``beta`` line 的 indicator。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(OLS_BetaN, period=10)
    '''
    _mindatas = 2  # 确保至少传入 2 个 data feed

    packages = (
        ('pandas', 'pd'),
    )

    lines = ('beta',)
    params = (('period', 10),)

    def next(self):
        y, x = (pd.Series(d.get(size=self.p.period)) for d in self.datas)
        r_beta = pd.ols(y=y, x=x, window_type='full_sample')
        self.lines.beta[0] = r_beta.beta['x']


class CointN(PeriodN):
    '''
    为传入 data feed 在给定 ``period`` 上计算协整 score（coint_t）与 pvalue。

    依赖 ``pandas`` 与 ``statsmodels``（用于 ``coint``）。

    Args:
        period: 协整检验窗口长度。
        trend: 传给 ``statsmodels.tsa.stattools.coint`` 的 trend 参数。

    Returns:
        CointN: 输出 ``score`` 与 ``pvalue`` line 的 indicator。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(CointN, period=10)
    '''
    _mindatas = 2  # 确保至少传入 2 个 data feed

    packages = (
        ('pandas', 'pd'),  # import pandas as pd
    )
    frompackages = (
        ('statsmodels.tsa.stattools', 'coint'),  # from st... import coint
    )

    lines = ('score', 'pvalue',)
    params = (
        ('period', 10),
        ('trend', 'c'),  # 见 statsmodel.tsa.statttools
    )

    def next(self):
        x, y = (pd.Series(d.get(size=self.p.period)) for d in self.datas)
        score, pvalue, _ = coint(x, y, trend=self.p.trend)
        self.lines.score[0] = score
        self.lines.pvalue[0] = pvalue
