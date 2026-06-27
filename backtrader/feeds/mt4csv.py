#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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


from . import GenericCSVData


class MT4CSVData(GenericCSVData):
    '''解析 `Metatrader4 <https://www.metaquotes.net/en/metatrader4>`_
    History Center 导出的 CSV 文件。

    该类基于 ``GenericCSVData``，并调整日期、时间和字段位置参数以匹配 MT4
    导出格式。

    Args:
        dataname: 要解析的文件名或 file-like 对象。

    Returns:
        bool: 成功解析一行时返回 ``True``。

    ---
    >>> data = MT4CSVData(dataname='mt4-history.csv')
    '''

    params = (
        ('dtformat', '%Y.%m.%d'),
        ('tmformat', '%H:%M'),
        ('datetime', 0),
        ('time',  1),
        ('open',  2),
        ('high',  3),
        ('low',   4),
        ('close', 5),
        ('volume', 6),
        ('openinterest', -1),
    )
