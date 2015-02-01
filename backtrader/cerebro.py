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
import metabase


class Cerebro(object):
    __metaclass__ = metabase.MetaParams

    params = (('preload', False), ('lookahead', 0),)

    def __init__(self):
        self.feeds = list()
        self.datas = list()
        self.strats = list()
        self.runstrats = list()
        self.brokers = list()

    def adddata(self, data, name=None):
        if name is not None:
            data._name = name
        self.datas.append(data)
        feed = data.getfeed()
        if feed and feed not in self.feeds:
            self.feeds.append(feed)

    def addstrategy(self, strategy, *args, **kwargs):
        self.strats.append((strategy, args, kwargs))

    def addbroker(self, broker):
        self.brokers.append(broker)

    def run(self):
        for feed in self.feeds:
            feed.start()

        for data in self.datas:
            data.extend(size=self.params.lookahead)
            data.start()
            if self.params.preload:
                data.preload()

        for broker in self.brokers:
            broker.start()

        for stratcls, sargs, skwargs in self.strats:
            sargs = self.datas + list(sargs)
            strat = stratcls(self, *sargs, **skwargs)
            strat.start()
            self.runstrats.append(strat)

        # FIXME: the loop check if all datas are producing bars and only
        # if none produces a bar, will the loop be over
        # But if data[0] is the clock and synchronizer it should be the only
        # one to be checked
        while [data.next() for data in self.datas].count(True):
            for broker in self.brokers:
                broker.next()

            for strat in self.runstrats:
                strat._next()

        for strat in self.runstrats:
            strat.stop()

        for data in self.datas:
            data.stop()

        for feed in self.feeds:
            feed.stop()
