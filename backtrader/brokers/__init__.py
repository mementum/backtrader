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

# 下列模块应在 __all__ 中定义要导出的对象，私有类/变量则使用 "_" 前缀

from .bbroker import BackBroker, BrokerBack

try:
    from .ibbroker import IBBroker
except ImportError:
    pass  # 用户可能未安装 ibpy

try:
    from .vcbroker import VCBroker
except ImportError:
    pass  # 用户可能未安装相关模块

try:
    from .oandabroker import OandaBroker
except ImportError as e:
    pass  # 用户可能未安装相关模块
