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

from collections import OrderedDict, defaultdict

from .py3 import values as py3lvalues


def Tree():
    '''创建可递归自动生成子节点的 ``defaultdict``。

    Returns:
        defaultdict: 默认值仍为 ``Tree`` 的嵌套字典。

    ---
    交互示例：
        >>> t = Tree()
        >>> t['a']['b'] = 1
        >>> t['a']['b']
        1
    '''
    return defaultdict(Tree)


class AutoDictList(dict):
    '''缺失 key 自动创建 ``list`` 的 dict。'''

    def __missing__(self, key):
        value = self[key] = list()
        return value


class DotDict(dict):
    '''支持以属性方式读取 item 的 dict。'''

    # 常规属性查找失败后，尝试从 dict 自身读取
    def __getattr__(self, key):
        if key.startswith('__'):
            return super(DotDict, self).__getattr__(key)
        return self[key]


class AutoDict(dict):
    '''缺失 key 自动创建嵌套 ``AutoDict`` 的 dict。

    ---
    交互示例：
        >>> d = AutoDict()
        >>> d.account.cash = 100
        >>> d['account']['cash']
        100
    '''

    _closed = False

    def _close(self):
        '''关闭自动创建行为，并递归关闭子 AutoDict。'''
        self._closed = True
        for key, val in self.items():
            if isinstance(val, (AutoDict, AutoOrderedDict)):
                val._close()

    def _open(self):
        '''重新打开自动创建行为。'''
        self._closed = False

    def __missing__(self, key):
        if self._closed:
            raise KeyError

        value = self[key] = AutoDict()
        return value

    def __getattr__(self, key):
        if False and key.startswith('_'):
            raise AttributeError

        return self[key]

    def __setattr__(self, key, value):
        if False and key.startswith('_'):
            self.__dict__[key] = value
            return

        self[key] = value


class AutoOrderedDict(OrderedDict):
    '''保持插入顺序且缺失 key 自动创建嵌套 ``AutoOrderedDict`` 的 dict。

    ---
    交互示例：
        >>> d = AutoOrderedDict()
        >>> d.stats.pnl = 12
        >>> d['stats']['pnl']
        12
    '''

    _closed = False

    def _close(self):
        '''关闭自动创建行为，并递归关闭子 AutoOrderedDict。'''
        self._closed = True
        for key, val in self.items():
            if isinstance(val, (AutoDict, AutoOrderedDict)):
                val._close()

    def _open(self):
        '''重新打开自动创建行为。'''
        self._closed = False

    def __missing__(self, key):
        if self._closed:
            raise KeyError

        # value = self[key] = type(self)()
        value = self[key] = AutoOrderedDict()
        return value

    def __getattr__(self, key):
        if key.startswith('_'):
            raise AttributeError

        return self[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
            return

        self[key] = value

    # 定义数学操作
    def __iadd__(self, other):
        if type(self) != type(other):
            return type(other)() + other

        return self + other

    def __isub__(self, other):
        if type(self) != type(other):
            return type(other)() - other

        return self - other

    def __imul__(self, other):
        if type(self) != type(other):
            return type(other)() * other

        return self + other

    def __idiv__(self, other):
        if type(self) != type(other):
            return type(other)() // other

        return self + other

    def __itruediv__(self, other):
        if type(self) != type(other):
            return type(other)() / other

        return self + other

    def lvalues(self):
        '''返回 values 的 list 兼容视图。'''
        return py3lvalues(self)
