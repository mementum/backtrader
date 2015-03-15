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

try:
    import matplotlib
    from matplotlib import pyplot
    import matplotlib.ticker
    from matplotlib.finance import volume_overlay, plot_day_summary2_ohlc, candlestick2_ohlc
    import matplotlib.font_manager as font_manager
except ImportError:
    matploblib = None

from .metabase import MetaParams


class PlotScheme(object):
    volume = True
    voloverlay = False
    volover_top = 2.5
    volover_bot =0.85
    rowsmajor = 5
    rowsminor = 1

    plotdist = 0.0

    grid = True

    style = 'line'
    loc = 'blue'
    barup = 'k'
    bardown = 'r'
    bartrans = 1.0

    volup = 'g'
    voldown = 'r'
    voltrans = 0.5

    subtxttrans = 0.66
    subtxtsize = 9

    legendtrans = 0.25
    legendind = True
    legendindloc = 'center left'
    skipmainsinglelabels = True

    hlinescolor = 'black'
    hlinesstyle = '--'
    hlineswidth = 1.0

    line0 = 'red'
    line1 = 'blue'
    line2 = 'green'
    line3 = 'brown'
    line4 = 'cyan'
    line5 = 'magenta'
    line6 = 'yellow'
    line7 = 'black'

    lines = [line0, line1, line2, line3, line4, line5, line6, line7]

    buymarker = '^'
    buylabel = 'Buy'
    buycolor = 'g'
    sellmarker = 'v'
    selllabel = 'Sell'
    sellcolor = 'r'
    buymarkersize = sellmarkersize = 8.0

    plotcashvalue = True


class Plot(six.with_metaclass(MetaParams, object)):

    params = (('scheme', PlotScheme()),)

    def __init__(self, **kwargs):
        if not matplotlib:
            raise ImportError('Please install matplotlib in order to enable plotting')

        for pname, pvalue in kwargs.items():
            setattr(self.params.scheme, pname, pvalue)


    def plotind(self, axis, daxis, rdt, datas, indplots, indsubplots, nrows, rows, rowspans):
        props = font_manager.FontProperties(size=self.params.scheme.subtxtsize)
        sharex = axis[0]

        for ind in indplots:
            if ind.plotinfo.subplot:
                ax = pyplot.subplot2grid((nrows, 1), (next(rows), 0), rowspan=next(rowspans), sharex=sharex)
                axis.append(ax)
                daxis[ind] = ax
            else: # plotted over data source (which may be data or indicator)
                ax = daxis[ind._clock]

            indlabel = ind.plotlabel()
            for lineidx in range(ind.size()):
                line = ind.lines[lineidx]
                linealias = ind.lines._getlinealias(lineidx)
                lineplotinfo = getattr(ind.plotlines, linealias)

                if ind.plotinfo.subplot:
                    # plotting on own subplot
                    if lineplotinfo._get('_plotskip', False):
                        # CHECK: Should we not add a "continue"
                        label = '_nolegend'
                    elif ind.size() == 1:
                        if self.params.scheme.skipmainsinglelabels:
                            label = '_nolegend'
                        elif not ind.plotinfo._get('singlelineslabels', False):
                            label = '_nolegend'
                        else:
                            label = linealias
                    else:
                        label = linealias
                else: # plotting on something else's plot
                    if not ind.plotinfo._get('linelabels', False):
                        label = '_nolegend' if lineidx else indlabel
                    else:
                        label = linealias

                    # plotting on someone else's ... indicator label to be shown

                plotkwargs = dict()
                if ind.plotinfo.subplot:
                    plotkwargs['color'] = self.params.scheme.lines[lineidx]

                plotkwargs.update(dict(aa=True, label=label))
                plotkwargs.update(**lineplotinfo._getkwargs(skip_=True))

                pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))
                pltmethod(rdt, line.plot(), **plotkwargs)

            if ind.plotinfo.subplot:
                ax.text(0.005, 0.97, indlabel, va='top', transform=ax.transAxes,
                        alpha=self.params.scheme.subtxttrans, fontsize=self.params.scheme.subtxtsize)

        # Go over the indicator subplots to put the legend in place
        # if done before ... indicators over indicators (ex: movavg on rsi) will not show
        # up in the legend, because such indicator is seen later in the previous loop
        for ind in indsubplots:
            ax = daxis[ind]

            # Let's do the ticks here in case they are automatic and an indicator on indicator
            # adds a bit to the automatic y scaling
            yticks = ind.plotinfo._get('yticks', None)
            if yticks is not None:
                ax.set_yticks(yticks)
            else:
                ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=4, prune='upper'))

            # This can be done also in the previous loop ... but since we do the ticks here
            hlines = ind.plotinfo._get('hlines', [])
            for hline in hlines:
                ax.axhline(hline,
                           color=self.params.scheme.hlinescolor,
                           ls=self.params.scheme.hlinesstyle,
                           lw=self.params.scheme.hlineswidth)

            if self.params.scheme.legendind and ind.plotinfo._get('legend', True):
                handles, labels = ax.get_legend_handles_labels()
                # Ensure that we have something to show
                if labels:
                    # Legend must be done here to ensure legend includes lines from ind on ind
                    legend = ax.legend(loc=self.params.scheme.legendindloc,
                                       shadow=False, fancybox=True, prop=props)
                    if legend:
                        legend.get_frame().set_alpha(self.params.scheme.legendtrans)

    def plot(self, strategy):
        if not strategy.datas:
            return

        fig = pyplot.figure(0)
        props = font_manager.FontProperties(size=self.params.scheme.subtxtsize)

        rowspans = list()

        obplots = [ob for ob in strategy.getobservers() if ob.plotinfo.plot]
        obsubplots = [ob for ob in obplots if ob.plotinfo.subplot]
        obsize = len(obsubplots)
        rowspans += [self.params.scheme.rowsminor] * obsize

        datasize = len(strategy.datas)
        rowspans += [self.params.scheme.rowsmajor]
        rowspans += [self.params.scheme.rowsminor] * (datasize - 1)

        volsize = datasize * (not self.params.scheme.voloverlay)
        rowspans += [self.params.scheme.rowsminor] * volsize

        datasize += volsize

        indplots = [ind for ind in strategy.getindicators() if ind.plotinfo.plot]
        indsubplots = [ind for ind in indplots if ind.plotinfo.subplot]
        indsize = len(indsubplots)
        rowspans += [self.params.scheme.rowsminor] * len(indsubplots)

        nrows = sum(rowspans)
        rows = [0] + [sum(rowspans[:i+1]) for i in range(len(rowspans) - 1)]

        roworder = [0, obsize, datasize, indsize]
        roworder = [sum(roworder[:i+1]) for i in range(len(roworder))]
        roworder = iter(roworder)

        r1, r2 = next(roworder), next(roworder)
        rowsob = iter(rows[r1:r2])
        rowspansob = iter(rowspans[r1:r2])

        r1, r2 = r2, next(roworder)
        rowsdata = iter(rows[r1:r2])
        rowspansdata = iter(rowspans[r1:r2])

        r1, r2 = r2, next(roworder)
        rowsind = iter(rows[r1:r2])
        rowspansind = iter(rowspans[r1:r2])

        # Keep a reference of the created ax to add plots (like moving average) to existing data
        # NOTE: a single "OrderedDict" can also do the trick
        axis = list()
        daxis = dict()

        # if "dates" are passed, matploblib adds non-existing dates (ie weekends) creating gaps
        # passing only the index number and combined with a formatter, only those are needed
        dt = strategy._clock.datetime.plot()
        rdt = range(len(strategy._clock.datetime))

        sharex = None
        for data in strategy.datas:
            ax = pyplot.subplot2grid((nrows, 1), (next(rowsdata), 0), rowspan=next(rowspansdata), sharex=sharex)
            sharex = sharex or ax # put just the first one in
            axis.append(ax)
            daxis[data] = ax

            closes = data.close.plot()
            opens = data.open.plot()

            if self.params.scheme.style.startswith('line'):
                ax.plot(rdt, closes, aa=True, label='_nolegend_')
            else:
                highs = data.high.plot()
                lows = data.low.plot()
                if self.params.scheme.style.startswith('candle'):
                    candlestick2_ohlc(ax, opens, highs, lows, closes, width=1.0,
                                      colorup=self.params.scheme.barup,
                                      colordown=self.params.scheme.bardown,
                                      alpha=self.params.scheme.bartrans)
                elif self.params.scheme.style.startswith('bar') or True:
                    # final default option -- should be "else"
                    plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize=4,
                                           colorup=self.params.scheme.barup,
                                           colordown=self.params.scheme.bardown)

            ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(prune='upper'))

            if self.params.scheme.volume:
                volumes = data.volume.plot()
                # Do only plot if a volume actually exists
                # This could be done in advance to actually tighten the chart if some data has no volume
                if max(volumes):
                    if self.params.scheme.voloverlay:
                        # Push the data upwards
                        bot, top = axdata.get_ylim()
                        ax.set_ylim(bot * self.params.scheme.volover_bot, top)

                        # Clone the data ax
                        axvol = ax.twinx()
                    else:
                        # Create independent subplot
                        axvol = pyplot.subplot2grid((nrows, 1), (next(rowsdata), 0),
                                                    rowspan=next(rowspansdata), sharex=sharex)
                        axis.append(axvol)

                    # Plot the volume (no matter if as overlay or standalone)
                    volalpha = 1.0 if not self.params.scheme.voloverlay else self.params.scheme.voltrans
                    bc = volume_overlay(axvol, opens, closes, volumes,
                                        colorup=self.params.scheme.volup,
                                        colordown=self.params.scheme.voldown,
                                        alpha=volalpha, width=1)

                    if self.params.scheme.voloverlay:
                        # Keep it at the bottom
                        bot, top = axvol.get_ylim()
                        axvol.set_ylim(bot, top * self.params.scheme.volover_top)
                        axvol.set_yticks([])
                    else:
                        # Cut the top of the y axis ticks
                        axvol.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(prune='upper'))

            # Make room for the labels at the top
            bot, top = ax.get_ylim()
            ax.set_ylim(bot, top * 1.01)

        # Plot the indicators
        self.plotind(axis, daxis, rdt, strategy.datas, indplots, indsubplots, nrows, rowsind, rowspansind)

        # Plot the observers
        self.plotind(axis, daxis, rdt, strategy.datas, obplots, obsubplots, nrows, rowsob, rowspansob)

        # NOTE: Plot Indicators/Observers before setting the legend of the "datas"
        # because some indicators will insert labes into the data legends

        # Data legends
        for data in strategy.datas:
            ax = daxis[data]
            legend = ax.legend(
                loc='upper center', shadow=False, fancybox=False, prop=props, numpoints=1, ncol=10)
            if legend:
                legend.get_frame().set_alpha(self.params.scheme.legendtrans)

        # Activate grid in all axes if requested
        for ax in axis:
            ax.grid(self.params.scheme.grid)

        # Date formatting for the x axis - only the last one needs it
        axis[-1].xaxis.set_major_formatter(MyFormatter(dt))
        axis[-1].xaxis.set_minor_formatter(MyFormatter2(dt))

        # Put the subplots as indicated by hspace (0 is touching each other)
        fig.subplots_adjust(hspace=self.params.scheme.plotdist, top=0.98, left=0.05, bottom=0.00, right=0.95)
        fig.autofmt_xdate()
        # Things must be tight along the x axis (to fill both ends)
        pyplot.autoscale(axis='x', tight=True)

    def show(self):
        pyplot.show()


class MyFormatter(matplotlib.ticker.Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        '''Return the label for time x at position pos'''
        ind = int(round(x))
        if ind >= self.lendates or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)


class MyFormatter2(matplotlib.ticker.Formatter):
    def __init__(self, dates, fmt='%b-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        '''Return the label for time x at position pos'''
        ind = int(round(x))
        if ind >= self.lendates or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)
