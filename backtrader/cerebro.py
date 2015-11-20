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

from .utils.py3 import map, range, zip, with_metaclass, string_types

from .broker import BrokerBack
from .metabase import MetaParams
from . import observers
from .writer import WriterFile
from .import num2date
from .utils import OrderedDict
from .resampler import DataResampler, DataReplayer


class Cerebro(with_metaclass(MetaParams, object)):
    '''
    Params:

      - ``preload`` (default: True)

        Whether to preload the different ``datas`` passed to cerebro for the
        Strategies

      - ``runonce`` (default: True)

        Run ``Indicators`` in vectorized mode to speed up the entire system.
        Strategies and Observers will always be run on an event based basis

      - ``maxcpus`` (default: None -> all available cores)

         How many cores to use simultaneously for optimization

      - stdstats (default: True)

        If True default Observers will be added: Broker (Cash and Value),
        Trades and BuySell

      - exactbars (default: False)

        If True, the system will switch to a mode in which all "lines" objects
        will use exactly the number of bars needed for the task. If a Simple
        Moving Average has a period of 30, the underlying data will have always
        a running buffer of 30 bars to allow the calculation of the Simple
        Moving Average

        Note:

          - This setting will deactivate ``preload`` and ``runonce``
          - Using this setting also deactivates plotting

      - ``writer`` (default: False)
        If set to True a default WriterFile will be created which will print to
        stdout. It will be added to the strategy (in addition to any other
        writers added by the user code)

      - ``tradehistory`` (default: False)
        If set to True, it will activate update event logging in each trade for
        all strategies. This can also be accomplished on a per strategy basis
        with the strategy method ``set_tradehistory``
    '''

    params = (
        ('preload', True),
        ('runonce', True),
        ('maxcpus', None),
        ('stdstats', True),
        ('lookahead', 0),
        ('exactbars', False),
        ('writer', False),
        ('tradehistory', False),
    )

    def __init__(self):
        self._dooptimize = False
        self.feeds = list()
        self.datas = list()
        self.datasbyname = collections.OrderedDict()
        self.strats = list()
        self.observers = list()
        self.analyzers = list()
        self.indicators = list()
        self.writers = list()

        self._broker = BrokerBack()

    @staticmethod
    def iterize(iterable):
        '''
        Handy function which turns things into things that can be iterated upon
        including iterables
        '''
        niterable = list()
        for elem in iterable:
            if isinstance(elem, string_types):
                elem = (elem,)
            elif not isinstance(elem, collections.Iterable):
                elem = (elem,)

            niterable.append(elem)

        return niterable

    def addwriter(self, wrtcls, *args, **kwargs):
        '''
        Adds an ``Writer`` class to the mix. Instantiation will be done at
        ``run`` time in cerebro
        '''
        self.writers.append((wrtcls, args, kwargs))

    def addindicator(self, indcls, *args, **kwargs):
        '''
        Adds an ``Indicator`` class to the mix. Instantiation will be done at
        ``run`` time in the passed strategies
        '''
        self.indicators.append((indcls, args, kwargs))

    def addanalyzer(self, ancls, *args, **kwargs):
        '''
        Adds an ``Analyzer`` class to the mix. Instantiation will be done at
        ``run`` time
        '''
        self.analyzers.append((ancls, args, kwargs))

    def addobserver(self, obscls, *args, **kwargs):
        '''
        Adds an ``Observer`` class to the mix. Instantiation will be done at
        ``run`` time
        '''
        self.observers.append((False, obscls, args, kwargs))

    def addobservermulti(self, obscls, *args, **kwargs):
        self.observers.append((True, obscls, args, kwargs))

    def adddata(self, data, name=None):
        '''
        Adds a ``Data Feed`` instance to the mix.

        if ``name`` is not None it will be put into ``data._name`` which is
        meant for decoration/plotting purposes.
        '''
        if name is not None:
            data._name = name

        self.datas.append(data)
        self.datasbyname[data._name] = data
        feed = data.getfeed()
        if feed and feed not in self.feeds:
            self.feeds.append(feed)

    def replaydata_old(self, dataname, name=None, **kwargs):
        '''
        Adds a ``Data Feed`` to be replayed by the system

        ``dataname`` will be passed as ``dataname`` to a on-the-fly generated
        ``DataReplayer``

        Any other kwargs like ``timeframe``, ``compression``, ``todate`` which
        are supported by ``DataReplayer`` will be passed transparently
        '''
        self.adddata(data=DataReplayer(dataname=dataname, **kwargs), name=name)

    def resampledata_old(self, dataname, name=None, **kwargs):
        '''
        Adds a ``Data Feed`` to be resample by the system

        ``dataname`` will be passed as ``dataname`` to a on-the-fly generated
        ``DataResampler``

        Any other kwargs like ``timeframe``, ``compression``, ``todate`` which
        are supported by ``DataResampler`` will be passed transparently
        '''
        self.adddata(data=DataResampler(dataname=dataname, **kwargs),
                     name=name)

    def replaydata(self, dataname, name=None, **kwargs):
        '''
        Adds a ``Data Feed`` to be replayed by the system

        ``dataname`` will be passed as ``dataname`` to a on-the-fly generated
        ``DataReplayer``

        Any other kwargs like ``timeframe``, ``compression``, ``todate`` which
        are supported by ``Replayer`` will be passed transparently
        '''
        dataname.replay(**kwargs)
        self.adddata(dataname, name=name)

    def resampledata(self, dataname, name=None, **kwargs):
        '''
        Adds a ``Data Feed`` to be resample by the system

        ``dataname`` will be passed as ``dataname`` to a on-the-fly generated
        ``DataResampler``

        Any other kwargs like ``timeframe``, ``compression``, ``todate`` which
        are supported by ``Resampler`` will be passed transparently
        '''
        dataname.resample(**kwargs)
        self.adddata(dataname, name=name)

    def optstrategy(self, strategy, *args, **kwargs):
        '''
        Adds a ``Strategy`` class to the mix for optimization. Instantiation
        will happen during ``run`` time.

        args and kwargs MUST BE iterables which hold the values to check.

        Example: if a Strategy accepts a parameter ``period``, for optimization
        purposes the call to ``optstrategy`` looks like:

          - cerebro.optstrategy(MyStrategy, period=(15, 25))

        or

          - cerebro.optstrategy(MyStrategy, period=range(15, 25))

        This will execute MyStrategy with ``period`` values 15 -> 25 (25 not
        included in the lot)

        If a parameter is passed but shall not be optimized the call looks
        like:

          - cerebro.optstrategy(MyStrategy, period=(15,))

        Notice that ``period`` is still passed as an iterable ... of just 1
        element

        ``backtrader`` will anyhow try to identify situations like:

          - cerebro.optstrategy(MyStrategy, period=15)

        and will create an internal pseudo-iterable if possible
        '''
        self._dooptimize = True
        args = self.iterize(args)
        optargs = itertools.product(*args)

        optkeys = list(kwargs)

        vals = self.iterize(kwargs.values())
        optvals = itertools.product(*vals)

        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)

        optkwargs = map(dict, okwargs1)

        it = itertools.product([strategy], optargs, optkwargs)
        self.strats.append(it)

    def addstrategy(self, strategy, *args, **kwargs):
        '''
        Adds a ``Strategy`` class to the mix for a single pass run.
        Instantiation will happen during ``run`` time.

        args and kwargs will be passed to the strategy as they are during
        instantiation.
        '''
        self.strats.append([(strategy, args, kwargs)])

    def setbroker(self, broker):
        '''
        Sets a specific ``broker`` instance for this strategy, replacing the
        one inherited from cerebro.
        '''
        self._broker = broker
        return broker

    def getbroker(self):
        '''
        Returns the broker instance.

        This is also available as a ``property`` by the name ``broker``
        '''
        return self._broker

    broker = property(getbroker, setbroker)

    def plot(self, plotter=None, numfigs=1, **kwargs):
        '''
        Plots the strategies inside cerebro

        If ``plotter`` is None a default ``Plot`` instance is created and
        ``kwargs`` are passed to it during instantiation.

        ``numfigs`` split the plot in the indicated number of charts reducing
        chart density if wished
        '''
        if self.p.exactbars:
            return

        if not plotter:
            from . import plot
            plotter = plot.Plot(**kwargs)

        for stratlist in self.runstrats:
            for strat in stratlist:
                plotter.plot(strat, numfigs=numfigs)

        plotter.show()

    def __call__(self, iterstrat):
        '''
        Used during optimization to pass the cerebro over the multiprocesing
        module without complains
        '''
        return self.runstrategies(iterstrat)

    def run(self, **kwargs):
        '''The core method to perform backtesting. Any ``kwargs`` passed to it
        will affect the value of the standard parameters ``Cerebro`` was
        instantiated with.

        If ``cerebro`` has not datas the method will immediately bail out.

        It has different return values:

          - For No Optimization: a list contanining instances of the Strategy
            classes added with ``addstrategy``

          - For Optimization: a list of lists which contain instances of the
            Strategy classes added with ``addstrategy``
        '''
        if not self.datas:
            return

        pkeys = self.params._getkeys()
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)

        self._dorunonce = self.p.runonce
        self._dopreload = self.p.preload

        if self.p.exactbars:
            # with exact bars no preload and no runonce are possible
            # Do not modify the params, but the internal values used
            self._dorunonce = False
            self._dopreload = False

        self.runwriters = list()

        # Add the system default writer if requested
        if self.p.writer is True:
            wr = WriterFile()
            self.runwriters.append(wr)

        # Instantiate any other writers
        for wrcls, wrargs, wrkwargs in self.writers:
            wr = wrcls(*wrargs, **wrkwargs)
            self.runwriters.append(wr)

        # Write down if any writer wants the full csv output
        self.writers_csv = any(map(lambda x: x.p.csv, self.runwriters))

        self.runstrats = list()
        iterstrats = itertools.product(*self.strats)
        if not self._dooptimize or self.p.maxcpus == 1:
            # If no optimmization is wished ... or 1 core is to be used
            # let's skip process "spawning"
            for iterstrat in iterstrats:
                runstrat = self.runstrategies(iterstrat)
                self.runstrats.append(runstrat)
        else:
            pool = multiprocessing.Pool(self.p.maxcpus or None)
            self.runstrats = list(pool.map(self, iterstrats))

        if not self._dooptimize:
            # avoid a list of list for regular cases
            return self.runstrats[0]

        return self.runstrats

    def runstrategies(self, iterstrat):
        '''
        Internal method invoked by ``run``` to run a set of strategies
        '''
        runstrats = list()
        self._broker.start()

        for feed in self.feeds:
            feed.start()

        if self.writers_csv:
            wheaders = list()
            for data in self.datas:
                if data.csv:
                    wheaders.extend(data.getwriterheaders())

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addheaders(wheaders)

        for stratcls, sargs, skwargs in iterstrat:
            sargs = self.datas + list(sargs)
            strat = stratcls(self, *sargs, **skwargs)
            if self.p.tradehistory:
                strat.set_tradehistory()
            runstrats.append(strat)

        # loop separated for clarity
        for strat in runstrats:
            if self.p.stdstats:
                strat._addobserver(False, observers.Broker)
                strat._addobserver(False, observers.BuySell)
                strat._addobserver(False, observers.Trades)

            for multi, obscls, obsargs, obskwargs in self.observers:
                strat._addobserver(multi, obscls, *obsargs, **obskwargs)

            for indcls, indargs, indkwargs in self.indicators:
                strat._addindicator(indcls, *indargs, **indkwargs)

            for ancls, anargs, ankwargs in self.analyzers:
                strat._addanalyzer(ancls, *anargs, **ankwargs)

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addheaders(strat.getwriterheaders())

            strat._start()

        if self.p.exactbars:
            for strat in runstrats:
                strat.ringbuffer()

        for data in self.datas:
            data.reset()
            if not self.p.exactbars:
                data.extend(size=self.params.lookahead)
            data.start()
            if self._dopreload:
                data.preload()

        for writer in self.runwriters:
            writer.start()

        if self._dopreload and self._dorunonce:
            self._runonce(runstrats)
        else:
            self._runnext(runstrats)

        for strat in runstrats:
            strat._stop()

        for data in self.datas:
            data.stop()

        for feed in self.feeds:
            feed.stop()

        self.stop_writers(runstrats)

        return runstrats

    def stop_writers(self, runstrats):
        cerebroinfo = OrderedDict()
        datainfos = OrderedDict()
        for i, data in enumerate(self.datas):
            datainfos['Data%d' % i] = data.getwriterinfo()

        cerebroinfo['Datas'] = datainfos

        stratinfos = dict()
        for strat in runstrats:
            stname = strat.__class__.__name__
            stratinfos[stname] = strat.getwriterinfo()

        cerebroinfo['Strategies'] = stratinfos

        for writer in self.runwriters:
            writer.writedict(dict(Cerebro=cerebroinfo))
            writer.stop()

    def _brokernotify(self):
        '''
        Internal method which kicks the broker and delivers any broker
        notification to the strategy
        '''
        self._broker.next()
        while self._broker.notifs:
            order = self._broker.notifs.popleft()
            order.owner._addnotification(order)

    def _runnext(self, runstrats):
        '''
        Actual implementation of run in full next mode. All objects have its
        ``next`` method invoke on each data arrival
        '''
        data0 = self.datas[0]
        d0ret = True
        while d0ret:
            d0ret = data0.next()
            if d0ret:
                for data in self.datas[1:]:
                    data.next(datamaster=data0)
            else:
                lastret = data0._last()
                for data in self.datas[1:]:
                    lastret += data._last(datamaster=data0)

                if not lastret:
                    # Only go extra round if something was changed by "lasts"
                    break

            self._brokernotify()

            for strat in runstrats:
                strat._next()

                self._next_writers(runstrats)

    def _runonce(self, runstrats):
        '''
        Actual implementation of run in vector mode.

        Strategies are still invoked on a pseudo-event mode in which ``next``
        is called for each data arrival
        '''
        for strat in runstrats:
            strat._once()

        # The default once for strategies does nothing and therefore
        # has not moved forward all datas/indicators/observers that
        # were homed before calling once, Hence no "need" to do it
        # here again, because pointers are at 0
        data0 = self.datas[0]
        datas = self.datas[1:]
        for i in range(data0.buflen()):
            data0.advance()
            for data in datas:
                data.advance(datamaster=data0)

            self._brokernotify()

            for strat in runstrats:
                strat._oncepost()

                self._next_writers(runstrats)

    def _next_writers(self, runstrats):
        if not self.runwriters:
            return

        if self.writers_csv:
            wvalues = list()
            for data in self.datas:
                if data.csv:
                    wvalues.extend(data.getwritervalues())

            for strat in runstrats:
                wvalues.extend(strat.getwritervalues())

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addvalues(wvalues)

                    writer.next()
