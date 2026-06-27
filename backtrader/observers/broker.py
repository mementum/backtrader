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

from .. import Observer


class Cash(Observer):
    '''该 observer 跟踪 broker 中当前的 cash 数量

    Args:
        无。

    ---
    交互示例:

    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(Cash)
    '''
    _stclock = True

    lines = ('cash',)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines[0][0] = self._owner.broker.getcash()


class Value(Observer):
    '''该 observer 跟踪 broker 中当前的 portfolio value，包括 cash

    Args:
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 value 是基于总净资产 value 还是 fund value。
            参见 broker 文档中的 ``set_fundmode``。将其设为 ``True`` 或
            ``False`` 可指定具体行为。

    ---
    交互示例:

    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(Value, fund=False)
    '''
    _stclock = True

    params = (
        ('fund', None),
    )

    lines = ('value',)

    plotinfo = dict(plot=True, subplot=True)

    def start(self):
        if self.p.fund is None:
            self._fundmode = self._owner.broker.fundmode
        else:
            self._fundmode = self.p.fund

    def next(self):
        if not self._fundmode:
            self.lines[0][0] = self._owner.broker.getvalue()
        else:
            self.lines[0][0] = self._owner.broker.fundvalue


class Broker(Observer):
    '''该 observer 跟踪 broker 中当前的 cash 数量和 portfolio value
    （包括 cash）

    Args:
        fund: 如果为 ``None``，会自动检测 broker 的实际 fundmode。设为
            ``True`` 时按 fund value 展示，设为 ``False`` 时按普通 broker
            value/cash 展示。

    ---
    交互示例:

    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(Broker)
    '''
    _stclock = True

    params = (
        ('fund', None),
    )

    alias = ('CashValue',)
    lines = ('cash', 'value')

    plotinfo = dict(plot=True, subplot=True)

    def start(self):
        if self.p.fund is None:
            self._fundmode = self._owner.broker.fundmode
        else:
            self._fundmode = self.p.fund

        if self._fundmode:
            self.plotlines.cash._plotskip = True
            self.plotlines.value._name = 'FundValue'

    def next(self):
        if not self._fundmode:
            self.lines.value[0] = value = self._owner.broker.getvalue()
            self.lines.cash[0] = self._owner.broker.getcash()
        else:
            self.lines.value[0] = self._owner.broker.fundvalue


class FundValue(Observer):
    '''该 observer 跟踪当前类 fund value

    Args:
        无。

    ---
    交互示例:

    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(FundValue)
    '''
    _stclock = True

    alias = ('FundShareValue', 'FundVal')
    lines = ('fundval',)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines.fundval[0] = self._owner.broker.fundvalue


class FundShares(Observer):
    '''该 observer 跟踪当前类 fund shares

    Args:
        无。

    ---
    交互示例:

    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(FundShares)
    '''
    _stclock = True

    lines = ('fundshares',)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines.fundshares[0] = self._owner.broker.fundshares
