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

import six

from .broker import BrokerBack
from .metabase import MetaParams
from . import plot


class Cerebro(six.with_metaclass(MetaParams, object)):

    params = (
        ('preload', True),
        ('runonce', True),
        ('lookahead', 0),
    )

    def __init__(self):
        self.feeds = list()
        self.datas = list()
        self.strats = list()
        self.runstrats = list()
        self._broker = BrokerBack()

    def adddata(self, data, name=None):
        if name is not None:
            data._name = name
        self.datas.append(data)
        feed = data.getfeed()
        if feed and feed not in self.feeds:
            self.feeds.append(feed)

    def addstrategy(self, strategy, *args, **kwargs):
        self.strats.append((strategy, args, kwargs))

    def setbroker(self, broker):
        self._broker = broker
        return broker

    def getbroker(self):
        return self._broker

    broker = property(getbroker, setbroker)

    def plot(self, plotter=None, **kwargs):
        plotter = plotter or plot.Plot(**kwargs)

        for strat in self.runstrats:
            plotter.plot(strat)

        plotter.show()

    def run(self):
        if not self.datas:
            return

        self._broker.start()

        for feed in self.feeds:
            feed.start()

        for data in self.datas:
            data.extend(size=self.params.lookahead)
            data.start()
            if self.params.preload:
                data.preload()

        for stratcls, sargs, skwargs in self.strats:
            sargs = self.datas + list(sargs)
            strat = stratcls(self, *sargs, **skwargs)
            self.runstrats.append(strat)

        for strat in self.runstrats: # loop separated for clarity
            strat.start()

        if self.params.preload and self.params.runonce:
            self._runonce()
        else:
            self._runnext()

        for strat in self.runstrats:
            strat.stop()

        for data in self.datas:
            data.stop()

        for feed in self.feeds:
            feed.stop()

    def _brokernotify(self):
        self._broker.next()
        while self._broker.notifs:
            order = self._broker.notifs.popleft()
            order.owner._addnotification(order)

    def _runnext(self):
        while self.datas[0].next():
            for data in self.datas[1:]:
                data.next()

            self._brokernotify()

            for strat in self.runstrats:
                strat._next()

    def _runonce(self):
        for strat in self.runstrats:
            strat._once()

        # The default once for strategies does nothing and therefore has not moved
        # forward all datas/indicators/observers that were homed before calling once
        # Hence no "need" to do it here again, because pointers are at 0

        for i in range(self.datas[0].buflen()):
            for data in self.datas:
                data.advance()

            self._brokernotify()

            for strat in self.runstrats:
                strat._oncepost()
