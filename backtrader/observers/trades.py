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

import uuid

from .. import Observer
from ..utils.py3 import with_metaclass

from ..trade import Trade


class Trades(Observer):
    '''跟踪完整 trade，并在 trade 关闭时绘制对应 PnL 的 observer。

    当 position 从 0（或穿越 0）变为 X 时，trade 被视为打开；当它回到 0
    （或反方向穿越 0）时，trade 被视为关闭。

    Args:
        pnlcomm (bool): 是否显示扣除 commission 后的 net profit/loss，默认
            ``True``。设为 ``False`` 时显示扣除 commission 前的 trade 结果。

    Returns:
        None: observer 通过 ``pnlplus`` 和 ``pnlminus`` lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(Trades)
    '''
    _stclock = True

    lines = ('pnlplus', 'pnlminus')

    params = dict(pnlcomm=True)

    plotinfo = dict(plot=True, subplot=True,
                    plotname='Trades - Net Profit/Loss',
                    plotymargin=0.10,
                    plothlines=[0.0])

    plotlines = dict(
        pnlplus=dict(_name='Positive',
                     ls='', marker='o', color='blue',
                     markersize=8.0, fillstyle='full'),
        pnlminus=dict(_name='Negative',
                      ls='', marker='o', color='red',
                      markersize=8.0, fillstyle='full')
    )

    def __init__(self):

        self.trades = 0

        self.trades_long = 0
        self.trades_short = 0

        self.trades_plus = 0
        self.trades_minus = 0

        self.trades_plus_gross = 0
        self.trades_minus_gross = 0

        self.trades_win = 0
        self.trades_win_max = 0
        self.trades_win_min = 0

        self.trades_loss = 0
        self.trades_loss_max = 0
        self.trades_loss_min = 0

        self.trades_length = 0
        self.trades_length_max = 0
        self.trades_length_min = 0

    def next(self):
        for trade in self._owner._tradespending:
            if trade.data not in self.ddatas:
                continue

            if not trade.isclosed:
                continue

            pnl = trade.pnlcomm if self.p.pnlcomm else trade.pnl

            if pnl >= 0.0:
                self.lines.pnlplus[0] = pnl
            else:
                self.lines.pnlminus[0] = pnl


class MetaDataTrades(Observer.__class__):
    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaDataTrades, cls).donew(*args, **kwargs)

        # 动态重新创建 lines
        if _obj.params.usenames:
            lnames = tuple(x._name for x in _obj.datas)
        else:
            lnames = tuple('data{}'.format(x) for x in range(len(_obj.datas)))

        # 生成新的 lines class
        linescls = cls.lines._derive(uuid.uuid4().hex, lnames, 0, ())

        # 实例化 lines
        _obj.lines = linescls()

        # 生成 plotlines 信息
        markers = ['o', 'v', '^', '<', '>', '1', '2', '3', '4', '8', 's', 'p',
                   '*', 'h', 'H', '+', 'x', 'D', 'd']

        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'b', 'g', 'r', 'c', 'm',
                  'y', 'k', 'b', 'g', 'r', 'c', 'm']

        basedict = dict(ls='', markersize=8.0, fillstyle='full')

        plines = dict()
        for lname, marker, color in zip(lnames, markers, colors):
            plines[lname] = d = basedict.copy()
            d.update(marker=marker, color=color)

        plotlines = cls.plotlines._derive(
            uuid.uuid4().hex, plines, [], recurse=True)
        _obj.plotlines = plotlines()

        return _obj, args, kwargs  # 返回已实例化对象和 args


class DataTrades(with_metaclass(MetaDataTrades, Observer)):
    '''按 data 分别绘制 closed trade PnL 的 observer。

    Args:
        usenames (bool): 是否使用 data 名称作为 line 名称，默认 ``True``。

    Returns:
        None: observer 通过动态生成的 data lines 暴露当前值。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addobserver(DataTrades)
    '''
    _stclock = True

    params = (('usenames', True),)

    plotinfo = dict(plot=True, subplot=True, plothlines=[0.0],
                    plotymargin=0.10)

    plotlines = dict()

    def next(self):
        for trade in self._owner._tradespending:
            if trade.data not in self.ddatas:
                continue

            if not trade.isclosed:
                continue

            self.lines[trade.data._id - 1][0] = trade.pnl
