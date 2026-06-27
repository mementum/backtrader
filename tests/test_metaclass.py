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
import testcommon

class TestFrompackages(testcommon.SampleParamsHolder):
    """验证继承使用 ``frompackages`` import 机制的基类不会破坏基类功能。"""
    def __init__(self):
        super(TestFrompackages, self).__init__()
        # 准备 lags array

def test_run(main=False):
    """实例化 TestFrompackages，并验证不会抛出异常。

    Bug 讨论：
    https://community.backtrader.com/topic/2661/frompackages-directive-functionality-seems-to-be-broken-when-using-inheritance
    """
    test = TestFrompackages()

if __name__ == '__main__':
    test_run(main=True)
