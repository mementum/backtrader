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
from broker import BrokerBack
import metabase
import plot


class Cerebro(object):
    __metaclass__ = metabase.MetaParams

    params = (('preload', True), ('lookahead', 0),)

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

    def run(self):
        if not self.datas:
            return

        for feed in self.feeds:
            feed.start()

        for data in self.datas:
            data.extend(size=self.params.lookahead)
            data.start()
            if self.params.preload:
                data.preload()

        self._broker.start()

        for stratcls, sargs, skwargs in self.strats:
            sargs = self.datas + list(sargs)
            strat = stratcls(self, *sargs, **skwargs)
            strat.start()
            self.runstrats.append(strat)

        while self.datas[0].next():
            for data in self.datas[1:]:
                data.next()

            self._broker.next()
            while self._broker.notifs:
                order = self._broker.notifs.popleft()
                order.owner._ordernotify(order)

            for strat in self.runstrats:
                strat._next()

        for strat in self.runstrats:
            strat.stop()

        for data in self.datas:
            data.stop()

        for feed in self.feeds:
            feed.stop()

    def plot(self, plotter=None, **kwargs):
        plotter = plotter or plot.Plot(**kwargs)

        for strat in self.runstrats:
            plotter.plot(strat)

        plotter.show()
