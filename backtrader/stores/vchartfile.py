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

import os.path

import backtrader as bt


class VChartFile(bt.Store):
    '''Visual Chart 二进制文件的 Store provider。

    Args:
        path: Visual Chart 数据文件目录。若为 ``None`` 且运行于 Windows，会查询注册表
            以定位 *Visual Chart* 文件根目录。

    Returns:
        VChartFile: 用于提供 Visual Chart 文件路径的 store。

    ---
    交互界面使用示范:

    >>> store = VChartFile(path='')
    >>> store.get_datapath()
    ''
    '''

    params = (
        ('path', None),
    )

    def __init__(self):
        self._path = self.p.path
        if self._path is None:
            self._path = self._find_vchart()

    @staticmethod
    def _find_vchart():
        # 查找 VisualChart 注册表项以获取数据目录；找不到则返回 ''
        VC_KEYNAME = r'SOFTWARE\VCG\Visual Chart 6\Config'
        VC_KEYVAL = 'DocsDirectory'
        VC_DATADIR = ['Realserver', 'Data', '01']

        VC_NONE = ''

        from backtrader.utils.py3 import winreg
        if winreg is None:
            return VC_NONE

        vcdir = None
        # 在常见根键中搜索目录
        for rkey in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE,):
            try:
                vckey = winreg.OpenKey(rkey, VC_KEYNAME)
            except WindowsError as e:
                continue

            # 尝试读取键值
            try:
                vcdir, _ = winreg.QueryValueEx(vckey, VC_KEYVAL)
            except WindowsError as e:
                continue
            else:
                break  # 找到 vcdir

        if vcdir is not None:  # 找到了内容
            vcdir = os.path.join(vcdir, *VC_DATADIR)
        else:
            vcdir = VC_NONE

        return vcdir

    def get_datapath(self):
        return self._path
