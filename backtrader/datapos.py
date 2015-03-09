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

from __future__ import absolute_import, division, print_function, unicode_literals


class Position(object):
    def __init__(self):
        self.size = 0
        self.price = 0.0

    def __len__(self):
        return self.size

    def update(self, size, price):
        newvalue = price * size
        oldsize = self.size
        oldvalue = self.price * oldsize
        self.size += size
        self.price = (oldvalue + newvalue) / (self.size or 1.0)

        if not self.size:
            opened, closed = 0, abs(oldsize)
        elif not oldsize:
            opened, closed = abs(size), 0
        elif oldsize > 0:
            if size > 0:
                opened, closed = size, 0
            elif newpos >= 0:
                opened, closed = 0, -size
            else: # newpos < 0
                opened, closed = -newpos, oldsize
        elif oldsize < 0:
            if size < 0:
                opened, closed = -size, 0
            elif newpos <= 0:
                opened, closed = 0, size
            else: # newpos > 0
                opened, closed = newpos, -oldsize

        return self.size, self.price, opened, closed
