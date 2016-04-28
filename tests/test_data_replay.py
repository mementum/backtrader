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

import testcommon

import backtrader as bt
import backtrader.indicators as btind

chkdatas = 1
chknext = 113
chkvals = [
    ['3836.453333', '3703.962333', '3741.802000']
]

chkmin = 30  # period will be in weeks
chkind = [btind.SMA]
chkargs = dict()


def test_run(main=False, exbar=False):
    data = testcommon.getdata(0)
    data.replay(timeframe=bt.TimeFrame.Weeks, compression=1)
    datas = [data]
    testcommon.runtest(datas,
                       testcommon.TestStrategy,
                       main=main,
                       plot=main,
                       chkind=chkind,
                       chkmin=chkmin,
                       chkvals=chkvals,
                       chknext=chknext,
                       chkargs=chkargs,
                       runonce=False,
                       preload=False,
                       exbar=exbar)


if __name__ == '__main__':
    for exbar in [False, -1, -2]:
        test_run(main=True, exbar=exbar)
