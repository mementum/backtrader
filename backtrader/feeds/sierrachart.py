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


from . import GenericCSVData


class SierraChartCSVData(GenericCSVData):
    '''解析 `SierraChart <http://www.sierrachart.com>`_ 导出的 CSV 文件。

    该类基于 ``GenericCSVData``，并将 ``dtformat`` 调整为 SierraChart 常见的
    ``'%Y/%m/%d'``。

    Args:
        dataname: 要解析的文件名或 file-like 对象。

    Returns:
        bool: 成功解析一行时返回 ``True``。

    ---
    >>> data = SierraChartCSVData(dataname='sierra.csv')
    '''

    params = (('dtformat', '%Y/%m/%d'),)
