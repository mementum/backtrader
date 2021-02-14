#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
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
import os
import testcommon

from backtrader import feeds as btfeeds
import backtrader.indicators as btind
import pandas

chkdatas = 1
chkvals = [
    ['4063.463000', '3644.444667', '3554.693333']
]

chkmin = 30  # period will be in weeks
chkind = [btind.SMA]
chkargs = dict()

modpath = os.path.dirname(os.path.abspath(__file__))
dataspath = '../datas'
datafiles = [
    '2006-day-001.txt',
    '2006-day-001-optix.txt',
]

FROMDATE = datetime.datetime(2006, 1, 1)
TODATE = datetime.datetime(2006, 12, 31)


class PandasDataOptix(btfeeds.PandasData):

    lines = ('optix_close', 'optix_pess', 'optix_opt',)
    params = (('optix_close', -1),
              ('optix_pess', -1),
              ('optix_opt', -1))


def getdata(index, noheaders=True):

    datapath = os.path.join(modpath, dataspath, datafiles[index])

    # Simulate the header row isn't there if noheaders requested
    skiprows = 1 if noheaders else 0
    header = None if noheaders else 0

    dataframe = pandas.read_csv(datapath,
                                skiprows=skiprows,
                                header=header,
                                parse_dates=True,
                                index_col=0)

    # Pass it to the backtrader datafeed and add it to the cerebro
    # Data in upper case for headers, nocase=True.
    if index:
        data = PandasDataOptix(dataname=dataframe, nocase=True)
    else:
        data = btfeeds.PandasData(dataname=dataframe, nocase=True)
    return data

def test_run(main=False):
    # Create list with bool possibilitys for:
    # PandasData and PandasOptix,
    # no headers,
    dc = [0, 1]
    data = [getdata(i, noheaders=nh) for i in dc for nh in dc]

    for runonce in [True, False]:
        datas = data
        testcommon.runtest(datas,
                           testcommon.TestStrategy,
                           main=main,
                           runonce=runonce,
                           plot=False,
                           chkind=chkind,
                           chkmin=chkmin,
                           chkvals=chkvals,
                           chkargs=chkargs)


if __name__ == '__main__':
    test_run(main=True)
