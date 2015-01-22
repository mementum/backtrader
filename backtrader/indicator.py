#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################
from lineiterator import LineIterator


class MetaIndicator(LineIterator.__metaclass__):
    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaIndicator, cls).dopreinit(_obj, *args, **kwargs)

        # 1st arg is the data source and therefore the ticking clock
        _obj._clock = args[0]

        return _obj, args, kwargs


class Indicator(LineIterator):
    __metaclass__ = MetaIndicator


def Naked(indicator):
    indicator._naked += 1
    return indicator
