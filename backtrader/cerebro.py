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

import collections
import itertools
import multiprocessing

import six
from six.moves import xrange

from .broker import BrokerBack
from .metabase import MetaParams
from . import observers


class Cerebro(six.with_metaclass(MetaParams, object)):

    params = (
        ('preload', True),
        ('runonce', True),
        ('lookahead', 0),
        ('maxcpus', None),
        ('stdstats', True),
    )

    def __init__(self):
        self._dooptimize = False
        self.feeds = list()
        self.datas = list()
        self.strats = list()
        self.observers = list()
        self.analyzers = list()
        self._broker = BrokerBack()

    @staticmethod
    def iterize(iterable):
        niterable = list()
        for elem in iterable:
            if isinstance(elem, six.string_types):
                elem = (elem,)
            elif not isinstance(elem, collections.Iterable):
                elem = (elem,)

            niterable.append(elem)

        return niterable

    def addanalyzer(self, ancls, *args, **kwargs):
        self.analyzers.append((ancls, args, kwargs))

    def addobserver(self, obscls, *args, **kwargs):
        self.observers.append((False, obscls, args, kwargs))

    def addobservermulti(self, obscls, *args, **kwargs):
        self.observers.append((True, obscls, args, kwargs))

    def adddata(self, data, name=None):
        if name is not None:
            data._name = name
        self.datas.append(data)
        feed = data.getfeed()
        if feed and feed not in self.feeds:
            self.feeds.append(feed)

    def optstrategy(self, strategy, *args, **kwargs):
        self._dooptimize = True
        args = self.iterize(args)
        optargs = itertools.product(*args)

        optkeys = list(kwargs.keys())  # py2/3

        vals = self.iterize(kwargs.values())
        optvals = itertools.product(*vals)

        okwargs1 = six.moves.map(
            six.moves.zip, itertools.repeat(optkeys), optvals)

        optkwargs = six.moves.map(dict, okwargs1)

        it = itertools.product([strategy], optargs, optkwargs)
        self.strats.append(it)

    def addstrategy(self, strategy, *args, **kwargs):
        self.strats.append([(strategy, args, kwargs)])

    def setbroker(self, broker):
        self._broker = broker
        return broker

    def getbroker(self):
        return self._broker

    broker = property(getbroker, setbroker)

    def plot(self, plotter=None, numfigs=1, **kwargs):
        if not plotter:
            from . import plot
            plotter = plot.Plot(**kwargs)

        for stratlist in self.runstrats:
            for strat in stratlist:
                plotter.plot(strat, numfigs=numfigs)

        plotter.show()

    def __call__(self, iterstrat):
        return self.runstrategies(iterstrat)

    def run(self, **kwargs):
        if not self.datas:
            return

        pkeys = self.params._getkeys()
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)

        self.runstrats = list()
        iterstrats = itertools.product(*self.strats)
        if not self._dooptimize or self.p.maxcpus == 1:
            # If no optimmization is wished ... or 1 core is to be used
            # let's skip process "spawning"
            for iterstrat in iterstrats:
                runstrat = self.runstrategies(iterstrat)
                self.runstrats.append(runstrat)
        else:
            pool = multiprocessing.Pool(self.p.maxcpus)
            self.runstrats = list(pool.map(self, iterstrats))

        if not self._dooptimize:
            # avoid a list of list for regular cases
            return self.runstrats[0]

        return self.runstrats

    def runstrategies(self, iterstrat):
        runstrats = list()
        self._broker.start()

        for feed in self.feeds:
            feed.start()

        for data in self.datas:
            data.reset()
            data.extend(size=self.params.lookahead)
            data.start()
            if self.params.preload:
                data.preload()

        for stratcls, sargs, skwargs in iterstrat:
            sargs = self.datas + list(sargs)
            strat = stratcls(self, *sargs, **skwargs)
            runstrats.append(strat)

        # loop separated for clarity
        for strat in runstrats:
            if self.p.stdstats:
                strat._addobserver(False, observers.Broker)
                strat._addobserver(False, observers.BuySell)
                strat._addobserver(False, observers.Trades)

            for multi, obscls, obsargs, obskwargs in self.observers:
                strat._addobserver(multi, obscls, *obsargs, **obskwargs)

            for ancls, anargs, ankwargs in self.analyzers:
                strat._addanalyzer(ancls, *anargs, **ankwargs)

            strat._start()

        if self.params.preload and self.params.runonce:
            self._runonce(runstrats)
        else:
            self._runnext(runstrats)

        for strat in runstrats:
            strat._stop()

        for data in self.datas:
            data.stop()

        for feed in self.feeds:
            feed.stop()

        return runstrats

    def _brokernotify(self):
        self._broker.next()
        while self._broker.notifs:
            order = self._broker.notifs.popleft()
            order.owner._addnotification(order)

    def _runnext(self, runstrats):
        data0 = self.datas[0]
        while data0.next():
            for data in self.datas[1:]:
                data.next(datamaster=data0)

            self._brokernotify()

            for strat in runstrats:
                strat._next()

    def _runonce(self, runstrats):
        for strat in runstrats:
            strat._once()

        # The default once for strategies does nothing and therefore
        # has not moved forward all datas/indicators/observers that
        # were homed before calling once, Hence no "need" to do it
        # here again, because pointers are at 0
        data0 = self.datas[0]
        datas = self.datas[1:]
        for i in xrange(data0.buflen()):
            data0.advance()
            for data in datas:
                data.advance(data0)

            self._brokernotify()

            for strat in runstrats:
                strat._oncepost()
