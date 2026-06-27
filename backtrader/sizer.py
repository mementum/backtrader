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

from .utils.py3 import with_metaclass

from .metabase import MetaParams


class Sizer(with_metaclass(MetaParams, object)):
    '''*Sizers* 的基类。任何 *sizer* 都应继承该类并覆盖 ``_getsizing`` 方法。

    成员属性:

      - ``strategy``: 由使用该 sizer 的 strategy 设置

        可访问 strategy 的完整 api。例如，如果 ``_getsizing`` 需要实际 data
        position，可以使用::

           position = self.strategy.getposition(data)

      - ``broker``: 由使用该 sizer 的 strategy 设置

        可访问复杂 sizer 可能需要的信息，例如 portfolio value 等。

    ---
    交互示例:

    >>> class FixedSizer(Sizer):
    ...     def _getsizing(self, comminfo, cash, data, isbuy):
    ...         return 10
    >>> class Broker:
    ...     def getcommissioninfo(self, data):
    ...         return None
    ...     def getcash(self):
    ...         return 1000.0
    >>> sizer = FixedSizer()
    >>> sizer.set(strategy='strategy', broker=Broker())
    >>> sizer.getsizing(data='data0', isbuy=True)
    10
    '''
    strategy = None
    broker = None

    def getsizing(self, data, isbuy):
        '''返回给定 data 和买卖方向下的实际 size。

        Args:
            data: 操作目标 data。
            isbuy (bool): ``True`` 表示 buy 操作，``False`` 表示 sell 操作。

        Returns:
            int: 由 ``_getsizing`` 计算得到的实际 size。
        '''
        comminfo = self.broker.getcommissioninfo(data)
        return self._getsizing(comminfo, self.broker.getcash(), data, isbuy)

    def _getsizing(self, comminfo, cash, data, isbuy):
        '''子类必须覆盖该方法，以提供 sizing 功能。

        Args:
            comminfo: CommissionInfo 实例，包含该 data 的 commission 信息，并可
                用于计算 position value、operation cost 和 operation commission。

            cash (float): *broker* 当前可用 cash。

            data: 操作目标。

            isbuy (bool): *buy* 操作为 ``True``，*sell* 操作为 ``False``。

        Returns:
            int: 要执行的实际 size。如果返回 ``0``，则不会执行任何操作。

        返回值会使用其绝对值。

        '''
        raise NotImplementedError

    def set(self, strategy, broker):
        '''设置 sizer 所属的 strategy 和 broker。

        Args:
            strategy: 使用该 sizer 的 strategy。
            broker: strategy 对应的 broker。
        '''
        self.strategy = strategy
        self.broker = broker


SizerBase = Sizer  # alias for old naming
