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
# 来源：http://stackoverflow.com/questions/4126348/how-do-i-rewrite-this-function-to-implement-ordereddict/4127426#4127426
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import OrderedDict

from .py3 import iteritems


class OrderedDefaultdict(OrderedDict):
    '''保持插入顺序的 ``defaultdict``。

    Args:
        *args: 第一个位置参数可为 default factory，其余参数传给 ``OrderedDict``。
        **kwargs: 传给 ``OrderedDict`` 的初始键值。

    Returns:
        OrderedDefaultdict: 读取缺失 key 时可自动创建默认值的有序字典。

    ---
    交互示例：
        >>> d = OrderedDefaultdict(list)
        >>> d['orders'].append(1)
        >>> d['orders']
        [1]
    '''

    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # 可选：支持 pickle
        args = (self.default_factory,) if self.default_factory else ()
        return self.__class__, args, None, None, iteritems(self)
