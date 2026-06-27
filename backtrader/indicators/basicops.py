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

import functools
import math
import operator

from ..utils.py3 import map, range

from . import Indicator


class PeriodN(Indicator):
    '''
    接受 ``period`` 参数的 indicator 基类，用于统一最小周期设置。

    该类不定义 line；子类需要通过 ``super`` 或显式调用其 ``__init__``。
    '''
    params = (('period', 1),)

    def __init__(self):
        super(PeriodN, self).__init__()
        self.addminperiod(self.p.period)


class OperationN(PeriodN):
    '''
    按给定周期计算 ``func`` 的基类，用于逻辑可由 callable 表达的周期型 indicator。

    Note:
      子类必须提供可调用的 ``func`` 属性。

    Formula:
      - line = func(data, period)
    '''
    def next(self):
        self.line[0] = self.func(self.data.get(size=self.p.period))

    def once(self, start, end):
        dst = self.line.array
        src = self.data.array
        period = self.p.period
        func = self.func

        for i in range(start, end):
            dst[i] = func(src[i - period + 1: i + 1])


class BaseApplyN(OperationN):
    '''
    ApplyN 及类似类的基类，用于接收 ``func`` 参数并由 indicator 自身定义 line。

    ``func`` 通过具名参数（``kwarg``）传入，并按给定周期计算。

    Formula:
      - lines[0] = func(data, period)

    第 1 条 line（索引 0）之外的额外 line 不会自动计算。
    '''
    params = (('func', None),)

    def __init__(self):
        self.func = self.p.func
        super(BaseApplyN, self).__init__()


class ApplyN(BaseApplyN):
    '''
    按给定周期计算 ``func``。

    Args:
        period: 计算窗口长度。
        func: 接收窗口数据并返回结果的 callable。

    Returns:
        ApplyN: 输出 ``apply`` line 的 indicator。

    Formula:
      - line = func(data, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ApplyN, period=5, func=max)
    '''
    lines = ('apply',)


class Highest(OperationN):
    '''
    计算给定周期内 data 的最高值。

    使用内置 ``max`` 计算。

    Args:
        period: 计算窗口长度。

    Returns:
        Highest: 输出 ``highest`` line 的 indicator。

    Formula:
      - highest = max(data, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Highest, period=14)
    '''
    alias = ('MaxN',)
    lines = ('highest',)
    func = max


class Lowest(OperationN):
    '''
    计算给定周期内 data 的最低值。

    使用内置 ``min`` 计算。

    Args:
        period: 计算窗口长度。

    Returns:
        Lowest: 输出 ``lowest`` line 的 indicator。

    Formula:
      - lowest = min(data, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Lowest, period=14)
    '''
    alias = ('MinN',)
    lines = ('lowest',)
    func = min


class ReduceN(OperationN):
    '''
    对 ``period`` 个 data 点应用 ``function``，计算 reduce 结果。

    使用内置 ``reduce`` 以及子类定义的 ``func`` 完成计算。

    Args:
        function: 传给 ``functools.reduce`` 的二元 callable。
        period: 计算窗口长度。
        initializer: 可选的 reduce 初始值。

    Returns:
        ReduceN: 输出 ``reduced`` line 的 indicator。

    Formula:
      - reduced = reduce(function(data, period)), initializer=initializer)

    Notes:

      - 为模拟 Python ``reduce``，该 indicator 将 ``function`` 作为第 1 个非具名参数，
        不同于大多数只接受具名参数的 indicator。

    ---
    交互界面使用示范:

    >>> import operator
    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ReduceN, operator.add, period=5)
    '''
    lines = ('reduced',)
    func = functools.reduce

    def __init__(self, function, **kwargs):
        if 'initializer' not in kwargs:
            self.func = functools.partial(self.func, function)
        else:
            self.func = functools.partial(self.func, function,
                                          initializer=kwargs['initializer'])

        super(ReduceN, self).__init__()


class SumN(OperationN):
    '''
    计算给定周期内 data 值的总和。

    使用 ``math.fsum`` 而不是内置 ``sum``，以降低精度误差。

    Args:
        period: 计算窗口长度。

    Returns:
        SumN: 输出 ``sumn`` line 的 indicator。

    Formula:
      - sumn = sum(data, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(SumN, period=10)
    '''
    lines = ('sumn',)
    func = math.fsum


class AnyN(OperationN):
    '''
    如果 ``period`` 内任意值为非零（即 ``True``），line 值为 ``True``（存为 ``1.0``）。

    使用内置 ``any`` 计算。

    Args:
        period: 计算窗口长度。

    Returns:
        AnyN: 输出 ``anyn`` line 的 indicator。

    Formula:
      - anyn = any(data, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AnyN, period=3)
    '''
    lines = ('anyn',)
    func = any


class AllN(OperationN):
    '''
    如果 ``period`` 内所有值都为非零（即 ``True``），line 值为 ``True``（存为 ``1.0``）。

    使用内置 ``all`` 计算。

    Args:
        period: 计算窗口长度。

    Returns:
        AllN: 输出 ``alln`` line 的 indicator。

    Formula:
      - alln = all(data, period)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AllN, period=3)
    '''
    lines = ('alln',)
    func = all


class FindFirstIndex(OperationN):
    '''
    返回与 ``_evalfunc`` 生成条件相等的第一个 data 的回看索引。

    Args:
        period: 搜索窗口长度。
        _evalfunc: 用于从窗口数据中生成目标值的 callable。

    Returns:
        FindFirstIndex: 输出 ``index`` line 的 indicator。

    Note:
      返回索引按回看方向计算。0 表示当前 bar，1 表示前一根 bar。

    Formula:
      - index = first for which data[index] == _evalfunc(data)
    '''
    lines = ('index',)
    params = (('_evalfunc', None),)

    def func(self, iterable):
        m = self.p._evalfunc(iterable)
        return next(i for i, v in enumerate(reversed(iterable)) if v == m)


class FindFirstIndexHighest(FindFirstIndex):
    '''
    返回周期内第一个最高值的回看索引。

    Args:
        period: 搜索窗口长度。

    Returns:
        FindFirstIndexHighest: 输出 ``index`` line 的 indicator。

    Note:
      返回索引按回看方向计算。0 表示当前 bar，1 表示前一根 bar。

    Formula:
      - index = index of first data which is the highest

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(FindFirstIndexHighest, period=10)
    '''
    params = (('_evalfunc', max),)


class FindFirstIndexLowest(FindFirstIndex):
    '''
    返回周期内第一个最低值的回看索引。

    Args:
        period: 搜索窗口长度。

    Returns:
        FindFirstIndexLowest: 输出 ``index`` line 的 indicator。

    Note:
      返回索引按回看方向计算。0 表示当前 bar，1 表示前一根 bar。

    Formula:
      - index = index of first data which is the lowest

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(FindFirstIndexLowest, period=10)
    '''
    params = (('_evalfunc', min),)


class FindLastIndex(OperationN):
    '''
    返回与 ``_evalfunc`` 生成条件相等的最后一个 data 的回看索引。

    Args:
        period: 搜索窗口长度。
        _evalfunc: 用于从窗口数据中生成目标值的 callable。

    Returns:
        FindLastIndex: 输出 ``index`` line 的 indicator。

    Note:
      返回索引按回看方向计算。0 表示当前 bar，1 表示前一根 bar。

    Formula:
      - index = last for which data[index] == _evalfunc(data)
    '''
    lines = ('index',)
    params = (('_evalfunc', None),)

    def func(self, iterable):
        m = self.p._evalfunc(iterable)
        index = next(i for i, v in enumerate(iterable) if v == m)
        # iterable 范围为 0 -> period - 1。如果返回最后一个元素（当前 bar）
        # 且不减 1，则 period - index = 1；这里必须为 0。
        return self.p.period - index - 1


class FindLastIndexHighest(FindLastIndex):
    '''
    返回周期内最后一个最高值的回看索引。

    Args:
        period: 搜索窗口长度。

    Returns:
        FindLastIndexHighest: 输出 ``index`` line 的 indicator。

    Note:
      返回索引按回看方向计算。0 表示当前 bar，1 表示前一根 bar。

    Formula:
      - index = index of last data which is the highest

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(FindLastIndexHighest, period=10)
    '''
    params = (('_evalfunc', max),)


class FindLastIndexLowest(FindLastIndex):
    '''
    返回周期内最后一个最低值的回看索引。

    Args:
        period: 搜索窗口长度。

    Returns:
        FindLastIndexLowest: 输出 ``index`` line 的 indicator。

    Note:
      返回索引按回看方向计算。0 表示当前 bar，1 表示前一根 bar。

    Formula:
      - index = index of last data which is the lowest

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(FindLastIndexLowest, period=10)
    '''
    params = (('_evalfunc', min),)


class Accum(Indicator):
    '''
    计算 data 值的累计和。

    Args:
        seed: 累计初始值。

    Returns:
        Accum: 输出 ``accum`` line 的 indicator。

    Formula:
      - accum += data

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Accum, seed=0.0)
    '''
    alias = ('CumSum', 'CumulativeSum',)
    lines = ('accum',)
    params = (('seed', 0.0),)

    # xxxstart 方法使用 seed（起始值）和传入 data 构造第一个值。
    # 因为不需要初始回看值，所以 minperiod 保持为 1。

    def nextstart(self):
        self.line[0] = self.p.seed + self.data[0]

    def next(self):
        self.line[0] = self.line[-1] + self.data[0]

    def oncestart(self, start, end):
        dst = self.line.array
        src = self.data.array
        prev = self.p.seed

        for i in range(start, end):
            dst[i] = prev = prev + src[i]

    def once(self, start, end):
        dst = self.line.array
        src = self.data.array
        prev = dst[start - 1]

        for i in range(start, end):
            dst[i] = prev = prev + src[i]


class Average(PeriodN):
    '''
    计算给定 data 在指定周期内的算术平均值。

    Args:
        period: 计算窗口长度。

    Returns:
        Average: 输出 ``av`` line 的 indicator。

    Formula:
      - av = data(period) / period

    See also:
      - https://en.wikipedia.org/wiki/Arithmetic_mean

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Average, period=10)
    '''
    alias = ('ArithmeticMean', 'Mean',)
    lines = ('av',)

    def next(self):
        self.line[0] = \
            math.fsum(self.data.get(size=self.p.period)) / self.p.period

    def once(self, start, end):
        src = self.data.array
        dst = self.line.array
        period = self.p.period

        for i in range(start, end):
            dst[i] = math.fsum(src[i - period + 1:i + 1]) / period


class ExponentialSmoothing(Average):
    '''
    使用 exponential smoothing 计算给定 data 在指定周期内的平均值。

    初始种子值使用前 ``period`` 个 data 的普通 ArithmeticMean（Average）。

    Args:
        period: 计算窗口长度。
        alpha: 平滑因子；未提供时使用 EMA 默认值。

    Returns:
        ExponentialSmoothing: 输出 ``av`` line 的 indicator。

    Formula:
      - av = prev * (1 - alpha) + data * alpha

    See also:
      - https://en.wikipedia.org/wiki/Exponential_smoothing

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ExponentialSmoothing, period=10)
    '''
    alias = ('ExpSmoothing',)
    params = (('alpha', None),)

    def __init__(self):
        self.alpha = self.p.alpha
        if self.alpha is None:
            self.alpha = 2.0 / (1.0 + self.p.period)  # 默认 EMA 值

        self.alpha1 = 1.0 - self.alpha

        super(ExponentialSmoothing, self).__init__()

    def nextstart(self):
        # 从基类计算中获取种子值
        super(ExponentialSmoothing, self).next()

    def next(self):
        self.line[0] = self.line[-1] * self.alpha1 + self.data[0] * self.alpha

    def oncestart(self, start, end):
        # 从基类计算中获取种子值
        super(ExponentialSmoothing, self).once(start, end)

    def once(self, start, end):
        darray = self.data.array
        larray = self.line.array
        alpha = self.alpha
        alpha1 = self.alpha1

        # 种子值来自 oncestart 调用计算出的 SMA
        prev = larray[start - 1]
        for i in range(start, end):
            larray[i] = prev = prev * alpha1 + darray[i] * alpha


class ExponentialSmoothingDynamic(ExponentialSmoothing):
    '''
    使用动态 alpha 的 exponential smoothing 计算给定 data 的平均值。

    初始种子值使用前 ``period`` 个 data 的普通 ArithmeticMean（Average）。

    Args:
        period: 计算窗口长度。
        alpha: 可动态变化的 alpha line。

    Returns:
        ExponentialSmoothingDynamic: 输出 ``av`` line 的 indicator。

    Note:
      - alpha 是一个可动态计算的值数组。

    Formula:
      - av = prev * (1 - alpha) + data * alpha

    See also:
      - https://en.wikipedia.org/wiki/Exponential_smoothing

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(ExponentialSmoothingDynamic, period=10)
    '''
    alias = ('ExpSmoothingDynamic',)

    def __init__(self):
        super(ExponentialSmoothingDynamic, self).__init__()

        # Hack: alpha 是一个 "line"，带有 minperiod；由于该 indicator 不进行 line
        # 赋值，minperiod 不会被自动纳入，因此需要手动处理。
        minperioddiff = max(0, self.alpha._minperiod - self.p.period)
        self.lines[0].incminperiod(minperioddiff)

    def next(self):
        self.line[0] = \
            self.line[-1] * self.alpha1[0] + self.data[0] * self.alpha[0]

    def once(self, start, end):
        darray = self.data.array
        larray = self.line.array
        alpha = self.alpha.array
        alpha1 = self.alpha1.array

        # 种子值来自 oncestart 调用计算出的 SMA
        prev = larray[start - 1]
        for i in range(start, end):
            larray[i] = prev = prev * alpha1[i] + darray[i] * alpha[i]


class WeightedAverage(PeriodN):
    '''
    计算给定 data 在指定周期内的加权平均值。

    如未提供 weights，默认权重通常由具体子类设置，用于给近期数据更高权重。

    结果会乘以给定 ``coef``。

    Args:
        period: 计算窗口长度。
        coef: 结果缩放系数。
        weights: 应用于窗口数据的权重序列。

    Returns:
        WeightedAverage: 输出 ``av`` line 的 indicator。

    Formula:
      - av = coef * sum(mul(data, period), weights)

    See:
      - https://en.wikipedia.org/wiki/Weighted_arithmetic_mean

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(WeightedAverage, period=3, weights=(1.0, 2.0, 3.0))
    '''
    alias = ('AverageWeighted',)
    lines = ('av',)
    params = (('coef', 1.0), ('weights', tuple()),)

    def __init__(self):
        super(WeightedAverage, self).__init__()

    def next(self):
        data = self.data.get(size=self.p.period)
        dataweighted = map(operator.mul, data, self.p.weights)
        self.line[0] = self.p.coef * math.fsum(dataweighted)

    def once(self, start, end):
        darray = self.data.array
        larray = self.line.array
        period = self.p.period
        coef = self.p.coef
        weights = self.p.weights

        for i in range(start, end):
            data = darray[i - period + 1: i + 1]
            larray[i] = coef * math.fsum(map(operator.mul, data, weights))
