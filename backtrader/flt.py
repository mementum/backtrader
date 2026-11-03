#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
# Copyright (C) 2026 Dennis Hansen
#
# This file is part of slim-backtrader, a modified version of backtrader.
# Modified in 2026 by Dennis Hansen. See changelog.txt for the changes.
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


from .metabase import MetaParams

__all__ = ["Filter"]


class MetaFilter(MetaParams):
    pass


class Filter(metaclass=MetaParams):

    _firsttime = True

    def __init__(self, data):
        pass

    def __call__(self, data):
        if self._firsttime:
            self.nextstart(data)
            self._firsttime = False

        # True means next() removed the bar, and load() must fetch another
        return self.next(data)

    def nextstart(self, data):
        pass

    def next(self, data):
        pass
