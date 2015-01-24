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

class Cerebro(object):
    def __init__(self):
        self.datas = list()
        self.feeds = list()
        self.strats = list()
        self.brokers = list()

    def addfeed(self, feed):
        self.feeds.append(feed)
        self.datas.append(feed.getdata())

    def addstrategy(self, strategy, *args, **kwargs):
        self.strats.append((strategy, args, kwargs))

    def addbroker(self, broker):
        self.brokers.append(broker)

    def run(self):
        for feed in self.feeds:
            feed.start()

        for broker in self.brokers:
            broker.start()

        strats = list()
        for stratcls, sargs, skwargs in self.strats:
            sargs = self.datas + list(sargs)
            strat = stratcls(self, *sargs, **skwargs)
            strat.start()
            strats.append(strat)

        while not [feed for feed in self.feeds if not feed.next()]:
            for data in self.datas:
                data.docalc()

            for broker in self.brokers:
                broker.next()

            for strat in strats:
                strat._next()

        for strat in strats:
            strat.stop()

        for feed in self.feeds:
            feed.stop()

    def runonce(self):
        for feed in self.feeds:
            feed.start()

        for feed in self.feeds:
            feed.preload()

        for data in self.datas:
            # data.docalc() # FULL CALCULATION ??
            pass

        for strat in self.strats:
            strat.start()

        for strat in self.strats:
            strat._once()

        for strat in self.strats:
            strat.stop()

        for feed in self.feeds:
            feed.stop()
