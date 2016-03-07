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

import time

import testcommon

import backtrader as bt
import backtrader.indicators as btind


chkdatas = 1


class TestStrategy(bt.Strategy):
    params = dict(main=False)

    def __init__(self):
        btind.SMA()


def test_run(main=False):
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    cerebros = testcommon.runtest(datas,
                                  TestStrategy,
                                  main=main,
                                  plot=main,
                                  writer=(bt.WriterStringIO, dict(csv=True)))

    for cerebro in cerebros:
        writer = cerebro.runwriters[0]
        if main:
            # writer.out.seek(0)
            for l in writer.out:
                print(l.rstrip('\r\n'))

        else:
            lines = iter(writer.out)
            l = next(lines).rstrip('\r\n')
            assert l == '=' * 79

            count = 0
            while True:
                l = next(lines).rstrip('\r\n')
                if l[0] == '=':
                    break
                count += 1

            assert count == 256  # header + 256 lines data


if __name__ == '__main__':
    test_run(main=True)
