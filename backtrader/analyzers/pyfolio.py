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


import collections

import backtrader as bt
from backtrader.utils.py3 import items, iteritems

from . import TimeReturn, PositionsValue, Transactions, GrossLeverage


class PyFolio(bt.Analyzer):
    '''收集并转换为 ``pyfolio`` 兼容数据集的 analyzer。

    该 analyzer 使用 4 个子 analyzer:

      - ``TimeReturn``

        用于计算全局 portfolio value 的 returns

      - ``PositionsValue``

        用于计算每个 data 的 position value，并将 ``headers`` 和 ``cash`` 参数
        设为 ``True``

      - ``Transactions``

        用于记录每个 data 上的 transaction（size、price、value），并将
        ``headers`` 参数设为 ``True``

      - ``GrossLeverage``

        跟踪 gross leverage，即 strategy 已投入程度

    Args:
        timeframe: 传递给子 analyzer 的 timeframe，默认 ``bt.TimeFrame.Days``。
            如果为 ``None``，使用系统中第 1 个 data 的 timeframe。
        compression: 传递给子 analyzer 的 compression，默认 ``1``。如果为
            ``None``，使用系统中第 1 个 data 的 compression。

    Returns:
        dict: ``get_analysis`` 返回包含 ``returns``、``positions``、
        ``transactions`` 和 ``gross_lev`` 的字典。

    ``timeframe`` 和 ``compression`` 的默认值遵循 ``pyfolio`` 的行为：使用
    daily data，并由 pyfolio 进一步 upsample 生成年度收益等结果。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(PyFolio, _name='pyfolio')
    '''
    params = (
        ('timeframe', bt.TimeFrame.Days),
        ('compression', 1)
    )

    def __init__(self):
        dtfcomp = dict(timeframe=self.p.timeframe,
                       compression=self.p.compression)

        self._returns = TimeReturn(**dtfcomp)
        self._positions = PositionsValue(headers=True, cash=True)
        self._transactions = Transactions(headers=True)
        self._gross_lev = GrossLeverage()

    def stop(self):
        super(PyFolio, self).stop()
        self.rets['returns'] = self._returns.get_analysis()
        self.rets['positions'] = self._positions.get_analysis()
        self.rets['transactions'] = self._transactions.get_analysis()
        self.rets['gross_lev'] = self._gross_lev.get_analysis()

    def get_pf_items(self):
        '''返回可交给 ``pyfolio`` 继续处理的 4 元组。

        Returns:
            tuple: ``returns``、``positions``、``transactions``、
            ``gross_leverage``。

        因为这些对象会作为 ``pyfolio`` 的直接输入，本方法会局部导入
        ``pandas``，把内部 *backtrader* 结果转换成 *pandas DataFrames*。
        这是例如 ``pyfolio.create_full_tear_sheet`` 所期望的输入格式。

        如果未安装 ``pandas``，该方法会失败。
        '''
        # 保持局部导入，避免影响未安装 pandas 的环境
        import pandas
        from pandas import DataFrame as DF

        #
        # Returns
        cols = ['index', 'return']
        returns = DF.from_records(iteritems(self.rets['returns']),
                                  index=cols[0], columns=cols)
        returns.index = pandas.to_datetime(returns.index)
        returns.index = returns.index.tz_localize('UTC')
        rets = returns['return']
        #
        # Positions
        pss = self.rets['positions']
        ps = [[k] + v[-2:] for k, v in iteritems(pss)]
        cols = ps.pop(0)  # headers 位于第 1 条记录
        positions = DF.from_records(ps, index=cols[0], columns=cols)
        positions.index = pandas.to_datetime(positions.index)
        positions.index = positions.index.tz_localize('UTC')

        #
        # Transactions
        txss = self.rets['transactions']
        txs = list()
        # transactions 有公共 key（date），并且可能发生在多个 asset 上。
        # 字典中一个 key 对应一个 list of lists；每个子 list 包含一条
        # transaction 的字段，因此需要双层循环展开 list 间接层
        for k, v in iteritems(txss):
            for v2 in v:
                txs.append([k] + v2)

        cols = txs.pop(0)  # headers 位于第 1 条记录
        transactions = DF.from_records(txs, index=cols[0], columns=cols)
        transactions.index = pandas.to_datetime(transactions.index)
        transactions.index = transactions.index.tz_localize('UTC')

        # Gross Leverage
        cols = ['index', 'gross_lev']
        gross_lev = DF.from_records(iteritems(self.rets['gross_lev']),
                                    index=cols[0], columns=cols)

        gross_lev.index = pandas.to_datetime(gross_lev.index)
        gross_lev.index = gross_lev.index.tz_localize('UTC')
        glev = gross_lev['gross_lev']

        # 一起返回
        return rets, positions, transactions, glev
