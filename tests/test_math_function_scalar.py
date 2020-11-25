#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
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
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import math


try:
    time_clock = time.process_time
except:
    time_clock = time.clock

import backtrader as bt


class SlipTestStrategy(bt.SignalStrategy):
    params = (
        ("printdata", False),
        ("printops", False),
    )

    def log(self, txt, dt=None, nodate=False):
        if not nodate:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print("%s, %s" % (dt.isoformat(), txt))
        else:
            print("---------- %s" % (txt))

    def __init__(self):
        self.ma = bt.ind.EMA(period=10)
        self.cross = bt.ind.CrossOver(self.datas[0].close, self.ma)
        # Single logic
        self.lg = bt.Log(self.datas[0].close)
        self.cl = bt.Ceiling(self.datas[0].close)
        self.fl = bt.Floor(self.datas[0].close)
        self.cross_abs = bt.Abs(self.cross)

        # Check Multi still works
        self.mx = bt.Max(self.datas[0].close, self.datas[0].open)

    def start(self):

        if self.p.printdata:
            self.log("-------------------------", nodate=True)
            self.log("Starting test")

        self.tstart = time_clock()

    def stop(self):
        tused = time_clock() - self.tstart
        if self.p.printdata:
            self.log("Time used: {:.4f} seconds".format(tused))
            self.log("-------------------------")
        else:
            pass

    def next(self):
        if self.p.printdata:
            self.log(
                " open {:.2f} close {:.2f}, max {:.2f}, log {:5.3f}, ceiling {:5.3f}, floor {:5.3f}, "
                "cross {:2.0f} abs cross {:2.0f}".format(
                    self.datas[0].open[0],
                    self.datas[0].close[0],
                    self.mx[0],
                    self.lg[0],
                    self.cl[0],
                    self.fl[0],
                    self.cross[0],
                    self.cross_abs[0],
                )
            )

        # Test values
        # max
        assert self.mx[0] == max(self.datas[0].close[0], self.datas[0].open[0])
        # Log
        assert self.lg[0] == math.log10(self.datas[0].close[0])
        # ceiling
        assert self.cl[0] == math.ceil(self.datas[0].close[0])
        # floor
        assert self.fl[0] == math.floor(self.datas[0].close[0])
        # absolut value
        assert self.cross_abs[0] == math.fabs(self.cross[0])


def test_run(main=False):
    """ Test addition of scalar math functions to Backtrader. See backtrader2 pr#22 """

    cerebro = bt.Cerebro()

    if main == True:
        strat_kwargs = dict(printdata=True, printops=True)
    else:
        strat_kwargs = dict(printdata=False, printops=False)

    cerebro.addstrategy(SlipTestStrategy, **strat_kwargs)

    modpath = os.path.dirname(os.path.abspath(__file__))
    dataspath = "../datas"
    datafile = "2006-day-001.txt"
    datapath = os.path.join(modpath, dataspath, datafile)
    data0 = bt.feeds.GenericCSVData(
        dataname=datapath,
        dtformat=("%Y-%m-%d"),
        timeframe=bt.TimeFrame.Days,
        compression=1,
    )
    cerebro.adddata(data0)

    cerebro.run()


if __name__ == "__main__":
    test_run(main=True)
