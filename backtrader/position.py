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


from copy import copy


class Position(object):
    '''
    保存并更新 position 的 size 和 price。该对象不与任何具体资产
    绑定，只记录 size 和 price。

    成员属性:
      - size (int): position 当前 size
      - price (float): position 当前 price

    可以用 len(position) 测试 Position 实例，以判断 size 是否非零

    ---
    交互示例:

    >>> position = Position(size=10, price=100.0)
    >>> position.size, position.price
    (10, 100.0)
    >>> position.update(size=-4, price=105.0)
    (6, 100.0, 0, -4)
    >>> bool(position)
    True
    '''

    def __str__(self):
        items = list()
        items.append('--- Position Begin')
        items.append('- Size: {}'.format(self.size))
        items.append('- Price: {}'.format(self.price))
        items.append('- Price orig: {}'.format(self.price_orig))
        items.append('- Closed: {}'.format(self.upclosed))
        items.append('- Opened: {}'.format(self.upopened))
        items.append('- Adjbase: {}'.format(self.adjbase))
        items.append('--- Position End')
        return '\n'.join(items)

    def __init__(self, size=0, price=0.0):
        '''
        创建一个 position。

        Args:
            size (int): 初始 position size。正数表示 long，负数表示 short。
            price (float): 初始 position price。仅当 ``size`` 非零时生效。
        '''
        self.size = size
        if size:
            self.price = self.price_orig = price
        else:
            self.price = 0.0

        self.adjbase = None

        self.upopened = size
        self.upclosed = 0
        self.set(size, price)

        self.updt = None

    def fix(self, size, price):
        '''
        直接修正 position 的 size 和 price，不计算 open/close 变化。

        Args:
            size (int): 要设置的新 position size。
            price (float): 要设置的新 position price。

        Returns:
            bool: 如果 size 未发生变化则返回 ``True``，否则返回 ``False``。
        '''
        oldsize = self.size
        self.size = size
        self.price = price
        return self.size == oldsize

    def set(self, size, price):
        '''
        设置 position 的 size 和 price，并根据旧 size 计算本次 opened/closed。

        Args:
            size (int): 要设置的新 position size。
            price (float): 要设置的新 position price。

        Returns:
            tuple: ``(size, price, opened, closed)``，分别表示新的 position
            size、position price、本次打开/增加的数量，以及本次关闭/减少的数量。
        '''
        if self.size > 0:
            if size > self.size:
                self.upopened = size - self.size  # 新 10 - 旧 5 -> 5
                self.upclosed = 0
            else:
                # 同方向 min(0, 3) -> 0 / 反转 min(0, -3) -> -3
                self.upopened = min(0, size)
                # 同方向 min(10, 10 - 5) -> 5
                # 反转 min(10, 10 - -5) -> min(10, 15) -> 10
                self.upclosed = min(self.size, self.size - size)

        elif self.size < 0:
            if size < self.size:
                self.upopened = size - self.size  # ex: -5 - -3 -> -2
                self.upclosed = 0
            else:
                # 同方向 max(0, -5) -> 0 / 反转 max(0, 5) -> 5
                self.upopened = max(0, size)
                # 同方向 max(-10, -10 - -5) -> max(-10, -5) -> -5
                # 反转 max(-10, -10 - 5) -> max(-10, -15) -> -10
                self.upclosed = max(self.size, self.size - size)

        else:  # self.size == 0
            self.upopened = self.size
            self.upclosed = 0

        self.size = size
        self.price_orig = self.price
        if size:
            self.price = price
        else:
            self.price = 0.0

        return self.size, self.price, self.upopened, self.upclosed

    def __len__(self):
        return abs(self.size)

    def __bool__(self):
        return bool(self.size != 0)

    __nonzero__ = __bool__

    def clone(self):
        '''
        复制当前 position。

        Returns:
            Position: 一个带有相同 size 和 price 的新 Position 实例。
        '''
        return Position(size=self.size, price=self.price)

    def pseudoupdate(self, size, price):
        '''
        在副本上模拟一次 update，不修改当前 position。

        Args:
            size (int): 模拟更新的 position size 变化量。
            price (float): 模拟更新使用的 price。

        Returns:
            tuple: 与 ``update`` 相同，返回模拟后的
            ``(size, price, opened, closed)``。
        '''
        return Position(self.size, self.price).update(size, price)

    def update(self, size, price, dt=None):
        '''
        更新当前 position，并返回更新后的 size、price，以及用于
        open/close position 的单位数

        Args:
            size (int): 用于更新 position size 的数量
                size < 0: 发生了一次 sell 操作
                size > 0: 发生了一次 buy 操作

            price (float):
                必须始终为正数，以确保一致性

            dt (datetime.datetime): 可选的 datetime 标记，会记录到 position 上。

        Returns:
            tuple: 一个非命名 tuple，包含
              - size: 新的 position size，即已有 size 与 ``size`` 参数相加后的结果
              - price: 新的 position price。如果 position 增加，返回新的平均
                price；如果 position 减少，剩余 size 的 price 不变；如果
                position 关闭，price 归零；如果 position 反转，price 为参数
                中给出的 price
              - opened: ``size`` 参数中用于 open/increase position 的合约数量。
                position 可以从 0 打开，也可以由反转产生。如果发生反转，
                opened 会小于 ``size``，因为 ``size`` 的一部分已被用于 close
                现有 position
              - closed: ``size`` 参数中用于 close/reduce position 的单位数

            opened 和 closed 都与 "size" 参数保持相同符号，因为它们引用的
            都是 "size" 参数的一部分

        ---
        交互示例:

        >>> position = Position(size=10, price=100.0)
        >>> position.update(size=5, price=110.0)
        (15, 103.33333333333333, 5, 0)
        >>> position.update(size=-20, price=90.0)
        (-5, 90.0, -5, -15)
        '''
        self.datetime = dt  # 记录 datetime 更新 (datetime.datetime)

        self.price_orig = self.price
        oldsize = self.size
        self.size += size

        if not self.size:
            # 更新后关闭了已有 position
            opened, closed = 0, size
            self.price = 0.0
        elif not oldsize:
            # 更新后从 0 打开了 position
            opened, closed = size, 0
            self.price = price
        elif oldsize > 0:  # 已有 "long" position 被更新

            if size > 0:  # 增加 position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size > 0:  # 减少 position
                opened, closed = 0, size
                # self.price = self.price

            else:  # self.size < 0 # position 从正数反转为负数
                opened, closed = self.size, -oldsize
                self.price = price

        else:  # oldsize < 0 - 已有 short position 被更新

            if size < 0:  # 增加 position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size < 0:  # 减少 position
                opened, closed = 0, size
                # self.price = self.price

            else:  # self.size > 0 - position 从负数反转为正数
                opened, closed = self.size, -oldsize
                self.price = price

        self.upopened = opened
        self.upclosed = closed

        return self.size, self.price, opened, closed
