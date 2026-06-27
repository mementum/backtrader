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


from .metabase import MetaParams
from .utils.py3 import with_metaclass


__all__ = ['Filter']


class MetaFilter(MetaParams):
    '''Filter metaclass 的基类，用于承载参数元信息。'''
    pass


class Filter(with_metaclass(MetaParams, object)):
    '''data filter 的基类，用于在 data 推进时执行过滤逻辑。'''

    _firsttime = True

    def __init__(self, data):
        '''初始化 filter。

        Args:
            data: filter 绑定的数据源。
        '''
        pass

    def __call__(self, data):
        '''执行一次 filter 调用。'''
        if self._firsttime:
            self.nextstart(data)
            self._firsttime = False

        self.next(data)

    def nextstart(self, data):
        '''首次处理 data 时调用的 hook。'''
        pass

    def next(self, data):
        '''每次处理 data 时调用的 hook。'''
        pass
