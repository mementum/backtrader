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


class FixedSize(bt.Sizer):
    '''返回固定 size 的 sizer。

    可以通过 ``tranches`` 参数把 ``stake`` 拆成多份，用于分批建仓。

    Args:
        stake (int): 每次操作使用的基础 size，默认 ``1``。
        tranches (int): 分批数量，默认 ``1``。大于 ``1`` 时返回
            ``stake / tranches`` 的整数部分。

    Returns:
        int: ``_getsizing`` 返回固定 size 或分批后的 size。

    ---
    >>> sizer = FixedSize(stake=10)
    >>> sizer._getsizing(None, 1000.0, None, True)
    10
    >>> sizer = FixedSize(stake=10, tranches=2)
    >>> sizer._getsizing(None, 1000.0, None, True)
    5
    '''

    params = (('stake', 1),
              ('tranches', 1))

    def _getsizing(self, comminfo, cash, data, isbuy):
        if self.p.tranches > 1:
            return abs(int(self.p.stake / self.p.tranches))
        else:
            return self.p.stake

    def setsizing(self, stake):
        if self.p.tranches > 1:
            self.p.stake = abs(int(self.p.stake / self.p.tranches))
        else:
            self.p.stake = stake  # 旧方法，为 sample 兼容保留


SizerFix = FixedSize


class FixedReverser(bt.Sizer):
    '''返回固定 size，并在反手时返回双倍 size 的 sizer。

    无持仓时返回 ``stake``，已有持仓时返回 ``2 * stake``，便于一次操作完成
    平旧仓并开新仓。

    Args:
        stake (int): 开仓使用的基础 size，默认 ``1``。

    Returns:
        int: 当前无持仓时为 ``stake``；已有持仓时为 ``2 * stake``。

    ---
    >>> class Position:
    ...     size = 3
    >>> class Strategy:
    ...     def getposition(self, data):
    ...         return Position()
    >>> sizer = FixedReverser(stake=5)
    >>> sizer.strategy = Strategy()
    >>> sizer._getsizing(None, 1000.0, None, False)
    10
    '''
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.strategy.getposition(data)
        size = self.p.stake * (1 + (position.size != 0))
        return size


class FixedSizeTarget(bt.Sizer):
    '''返回固定 target size 的 sizer。

    该 sizer 适合配合 Target Orders 使用，尤其是
    ``cerebro.target_order_size()``。也可以通过 ``tranches`` 参数分批靠近
    目标 size。

    Args:
        stake (int): 目标 size，默认 ``1``。
        tranches (int): 分批数量，默认 ``1``。大于 ``1`` 时，每次最多增加
            ``stake / tranches`` 的整数部分。

    Returns:
        int: 目标 size，或在分批模式下不超过 ``stake`` 的下一步 target size。

    ---
    >>> class Position:
    ...     size = 4
    >>> class Strategy:
    ...     position = Position()
    >>> sizer = FixedSizeTarget(stake=10, tranches=2)
    >>> sizer.strategy = Strategy()
    >>> sizer._getsizing(None, 1000.0, None, True)
    9
    '''

    params = (('stake', 1),
              ('tranches', 1))

    def _getsizing(self, comminfo, cash, data, isbuy):
        if self.p.tranches > 1:
            size = abs(int(self.p.stake / self.p.tranches))
            return min((self.strategy.position.size + size), self.p.stake)
        else:
            return self.p.stake

    def setsizing(self, stake):
        if self.p.tranches > 1:
            size = abs(int(self.p.stake / self.p.tranches))
            self.p.stake = min((self.strategy.position.size + size),
                               self.p.stake)
        else:
            self.p.stake = stake  # 旧方法，为 sample 兼容保留
