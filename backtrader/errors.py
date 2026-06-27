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


__all__ = ['BacktraderError', 'StrategySkipError']


class BacktraderError(Exception):
    '''backtrader 异常的基类，用于统一承载框架内错误。'''
    pass


class StrategySkipError(BacktraderError):
    '''请求平台在回测中跳过当前 strategy。

    该异常应在 strategy 实例初始化（``__init__``）阶段抛出。
    '''
    pass


class ModuleImportError(BacktraderError):
    '''依赖模块缺失时抛出的异常。

    当某个类需要指定 module 才能工作，但该 module 无法 import 时使用。

    Args:
        message: 给调用方展示的错误信息。
        *args: 与缺失 module 相关的附加上下文。
    '''
    def __init__(self, message, *args):
        super(ModuleImportError, self).__init__(message)
        self.args = args


class FromModuleImportError(ModuleImportError):
    '''``from module import name`` 形式依赖缺失时抛出的异常。

    Args:
        message: 给调用方展示的错误信息。
        *args: 与缺失对象相关的附加上下文。
    '''
    def __init__(self, message, *args):
        super(FromModuleImportError, self).__init__(message, *args)
