#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
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
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import os
import os.path
import sys

try:
    import backtrader as bt
    import backtrader.utils.flushfile
except ImportError:
    # append module root directory to sys.path
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import backtrader as bt
    import backtrader.utils.flushfile

    # Should any exception happen, then the module cannot be imported
    # let the exception propagate to signal the error


modpath = os.path.dirname(os.path.abspath(__file__))
dataspath = '../samples/datas/sample'
datafiles = [
    '2006-day-001.txt',
    '2006-week-001.txt',
]

DATAFEED = bt.feeds.BacktraderCSVData

FROMDATE = datetime.datetime(2006, 1, 1)
TODATE = datetime.datetime(2006, 12, 31)


def getdata(index, fromdate=FROMDATE, todate=TODATE):

    datapath = os.path.join(modpath, dataspath, datafiles[index])
    data = DATAFEED(
        dataname=datapath,
        fromdate=fromdate,
        todate=todate)

    return data


def runtest(datas, strategy,
            runonce=True, preload=True, plot=False, optimize=False,
            **kwargs):

    cerebro = bt.Cerebro(runonce=runonce, preload=preload)

    if isinstance(datas, bt.LineSeries):
        datas = [datas]
    for data in datas:
        cerebro.adddata(data)

    if not optimize:
        cerebro.addstrategy(strategy, **kwargs)
    else:
        cerebro.optstrategy(strategy, **kwargs)

    cerebro.run()
    if plot:
        cerebro.plot()


class TestStrategy(bt.Strategy):
    params = dict(main=False,
                  chkind=[],
                  inddata=[],
                  chkmin=1,
                  chknext=0,
                  chkvals=None,
                  chkargs=dict())

    def __init__(self):
        try:
            ind = self.p.chkind[0]
        except TypeError:
            chkind = [self.p.chkind]
        else:
            chkind = self.p.chkind

        if len(self.p.inddata):
            self.ind = chkind[0](*self.p.inddata, **self.p.chkargs)
        else:
            self.ind = chkind[0](self.data, **self.p.chkargs)

        for ind in chkind[1:]:
            ind(self.data)

        for data in self.datas[1:]:
            chkind[0](data, **self.p.chkargs)

            for ind in chkind[1:]:
                ind(data)

    def prenext(self):
        pass

    def nextstart(self):
        self.chkmin = len(self)
        super(TestStrategy, self).nextstart()

    def next(self):
        self.nextcalls += 1

        if self.p.main:
            dtstr = self.data.datetime.date(0).strftime('%Y-%m-%d')
            print('%s - %d - %f' % (dtstr, len(self), self.ind[0]))

    def start(self):
        self.nextcalls = 0

    def stop(self):
        l = len(self.ind)
        mp = self.chkmin
        chkpts = [0, -l + mp, (-l + mp) // 2]

        if self.p.main:
            print('----------------------------------------')
            print('len ind %d == %d len self' % (l, len(self)))
            print('minperiod %d' % self.chkmin)
            print('self.p.chknext %d nextcalls %d'
                  % (self.p.chknext, self.nextcalls))

            print('chkpts are', chkpts)
            for chkpt in chkpts:
                dtstr = self.data.datetime.date(chkpt).strftime('%Y-%m-%d')
                print('chkpt %d -> %s' % (chkpt, dtstr))

            for lidx in range(self.ind.size()):
                chkvals = list()
                outtxt = '    ['
                for chkpt in chkpts:
                    valtxt = "'%f'" % self.ind.lines[lidx][chkpt]
                    outtxt += "'%s'," % valtxt
                    chkvals.append(valtxt)

                    outtxt = '    [' + ', '.join(chkvals) + '],'

                if lidx == self.ind.size() - 1:
                    outtxt = outtxt.rstrip(',')

                print(outtxt)

            print('vs')

            for chkval in self.p.chkvals:
                print(chkval)

        else:
            assert l == len(self)
            if self.p.chknext:
                assert self.p.chknext == self.nextcalls
            assert mp == self.p.chkmin
            for lidx, linevals in enumerate(self.p.chkvals):
                for i, chkpt in enumerate(chkpts):
                    chkval = '%f' % self.ind.lines[lidx][chkpt]
                    assert chkval == linevals[i]
