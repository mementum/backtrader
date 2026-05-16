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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import testcommon

import backtrader as bt


class BindLinesStrategy(bt.Strategy):
    params = dict(main=False)

    def __init__(self):
        self.sma = bt.ind.SMA(self.data, period=5)
        self.sma.bindlines()


def test_bindlines_python_310_collections_abc(main=False):
    data = testcommon.getdata(0,
                              fromdate=datetime.datetime(2006, 1, 1),
                              todate=datetime.datetime(2006, 1, 31))

    testcommon.runtest([data],
                       BindLinesStrategy,
                       runonce=False,
                       preload=False,
                       exbar=False,
                       main=main)


if __name__ == '__main__':
    test_bindlines_python_310_collections_abc(main=True)
