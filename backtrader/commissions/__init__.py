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

from ..comminfo import CommInfoBase


class CommInfo(CommInfoBase):
    '''CommissionInfo 的兼容变体，使用 ``xx%`` 表示百分比而不是 ``0.xx``。'''
    pass


class CommInfo_Futures(CommInfoBase):
    '''futures-like commission scheme 的基类。'''
    params = (
        ('stocklike', False),
    )


class CommInfo_Futures_Perc(CommInfo_Futures):
    '''按百分比计算的 futures-like commission scheme。'''
    params = (
        ('commtype', CommInfoBase.COMM_PERC),
    )


class CommInfo_Futures_Fixed(CommInfo_Futures):
    '''按固定金额计算的 futures-like commission scheme。'''
    params = (
        ('commtype', CommInfoBase.COMM_FIXED),
    )


class CommInfo_Stocks(CommInfoBase):
    '''stock-like commission scheme 的基类。'''
    params = (
        ('stocklike', True),
    )


class CommInfo_Stocks_Perc(CommInfo_Stocks):
    '''按百分比计算的 stock-like commission scheme。'''
    params = (
        ('commtype', CommInfoBase.COMM_PERC),
    )


class CommInfo_Stocks_Fixed(CommInfo_Stocks):
    '''按固定金额计算的 stock-like commission scheme。'''
    params = (
        ('commtype', CommInfoBase.COMM_FIXED),
    )
