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
import itertools

from lineiterator import LineIterator, Parameter


class MetaIndicator(LineIterator.__metaclass__):

    def dopreinit(cls, obj, *args, **kwargs):
        obj, args, kwargs = super(MetaIndicator, cls).dopreinit(obj, *args, **kwargs)

        # 1st arg is the data source and therefore the ticking clock
        obj._clock = args[0]
        obj._id = Indicator._id.next()
        return obj, args, kwargs


class Indicator(LineIterator):
    __metaclass__ = MetaIndicator

    _id = itertools.count()


def Naked(indicator):
    indicator._naked += 1
    return indicator
