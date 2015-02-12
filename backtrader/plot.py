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
import itertools

try:
    import matplotlib
    from matplotlib import pyplot
    from matplotlib.ticker import Formatter, MaxNLocator
    from matplotlib.finance import volume_overlay
except ImportError:
    matploblib = None

import metabase


class Plot(object):
    __metaclass__ = metabase.MetaParams

    LineOnClose, OhlcBar, Candlestick = range(3)

    params = (
        ('style', LineOnClose),
        ('volume', True),
    )

    def __init__(self):
        if not matplotlib:
            raise ImportError('Please install matplotlib in order to enable plotting')

    def plot(self, strategy):
        indplots = [ind for ind in strategy._indicators if ind.plot]
        nsubplots = len(strategy.datas) + sum([ind.subplot for ind in indplots])
        fig, axis = pyplot.subplots(nsubplots, sharex=True)

        # if "dates" are passed, matploblib adds non-existing dates (ie weekends) creating gaps
        # passing only the index number and combined with a formatter, only those are needed
        dt = strategy._clock.datetime.plot()

        rdt = range(len(strategy._clock.datetime))

        i = itertools.count()
        for data in strategy.datas:
            # FIXME ... implement ohlc if so requested
            axdata = axis[i.next()]
            axdata.plot(rdt, data.close.plot())
            if self.params.volume:
                # Push the data upwards
                bot, top = axdata.get_ylim()
                axdata.set_ylim(bot * 0.80, top)

                # Plot the volume
                axvol = axdata.twinx()
                bc = volume_overlay(axvol,
                                    data.open.plot(), data.close.plot(), data.volume.plot(),
                                    colorup='g', alpha=0.33, width=1)
                axvol.add_collection(bc)
                # Keep it at the bottom
                bot, top = axvol.get_ylim()
                axvol.set_ylim(bot, top * 2)

        for ind in indplots:
            if ind.subplot:
                pltidx = i.next()
            elif ind._clock in strategy.datas:
                pltidx = strategy.datas.index(ind._clock)
            else: # must be another indicator
                offset = len(strategy.datas)
                pltidx = offset + indplots.index(ind._clock)

            indaxis = axis[pltidx]
            for ii in xrange(ind.size()):
                line = ind.lines[ii]
                pltmethod = getattr(indaxis, line.plotmethod, 'plot')
                pltmethod(rdt, line.plot(), aa=True, **line.plotargs)

            if ind.subplot:
                indaxis.set_ylabel(ind.__class__.__name__)
                indaxis.yaxis.set_major_locator(MaxNLocator(bins=5, prune='upper'))

        formatter = MyFormatter(dt)
        formatter2 = MyFormatter2(dt)

        for ax in axis:
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_minor_formatter(formatter2)
            ax.grid(True)

        fig.subplots_adjust(hspace=0.0, top=0.90, left=0.1, bottom=0.1, right=0.90)
        fig.autofmt_xdate()
        pyplot.autoscale(axis='x', tight=True)
        pyplot.show()


class MyFormatter(Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(round(x))
        if ind >= self.lendates or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)


class MyFormatter2(Formatter):
    def __init__(self, dates, fmt='%b-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(round(x))
        if ind >= self.lendates or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)
