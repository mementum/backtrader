#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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

import datetime

from .dateintern import _num2date, _date2num, time2num, num2time

__all__ = ('num2date', 'date2num', 'time2num', 'num2time')

try:
    import matplotlib.dates as mdates

except ImportError:
    num2date = _num2date
    date2num = _date2num
else:
    num2date = _num2date
    date2num = _date2num
    # num2date = mdates.num2date
    # date2num = mdates.date2num
