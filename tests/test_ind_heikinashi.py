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

chkdatas = 1
chkvals = [
    ['4119.466107', '3591.732500', '3578.625259'],
    ['4142.010000', '3638.420000', '3662.920000'],
    ['4119.466107', '3591.732500', '3578.625259'],
    ['4128.002500', '3614.670000', '3653.455000']
]

chkmin = 2
chkind = bt.ind.HeikinAshi


def test_run(main=False):
    if False:
        datas = [testcommon.getdata(i) for i in range(chkdatas)]
        testcommon.runtest(datas,
                           testcommon.TestStrategy,
                           main=main,
                           plot=main,
                           chkind=chkind,
                           chkmin=chkmin,
                           chkvals=chkvals)


if __name__ == '__main__':
    test_run(main=True)
