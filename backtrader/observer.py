#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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


from .lineiterator import LineIterator, ObserverBase, StrategyBase


class Observer(ObserverBase):
    _OwnerCls = StrategyBase
    _ltype = LineIterator.ObsType

    csv = True

    plotinfo = dict(plot=False, subplot=True)

    # An Observer is ideally always observing and that' why prenext calls
    # next. The behaviour can be overriden by subclasses
    def prenext(self):
        self.next()
