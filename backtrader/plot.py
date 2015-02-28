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
    import matplotlib.ticker
    from matplotlib.finance import volume_overlay, plot_day_summary2_ohlc, candlestick2_ohlc
    import matplotlib.font_manager as font_manager
except ImportError:
    matploblib = None

import metabase

class PlotScheme(object):
    volume = True
    voloverlay = False
    volover_top = 2.5
    volover_bot =0.85
    rowsmajor = 5
    rowsminor = 1

    plotdist = 0.0

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


class Plot(object):
    __metaclass__ = metabase.MetaParams

    params = (
        ('scheme', PlotScheme()),
    )

    def __init__(self, **kwargs):
        if not matplotlib:
            raise ImportError('Please install matplotlib in order to enable plotting')

        for pname, pvalue in kwargs.iteritems():
            setattr(self.params.scheme, pname, pvalue)


    def plot(self, strategy):
        dataslen = len(strategy.datas)
        if not dataslen:
            return

        fig = pyplot.figure(0)

        nrows = self.params.scheme.rowsmajor + (dataslen - 1) * self.params.scheme.rowsminor
        nrows += (not self.params.scheme.voloverlay) * dataslen * self.params.scheme.rowsminor
        indplots = [ind for ind in strategy._indicators if ind.plot]
        indsubplots = [ind for ind in indplots if ind.subplot]
        nrows += sum([ind.subplot for ind in indplots]) * self.params.scheme.rowsminor

        if self.params.scheme.plotcashvalue:
            nrows += len(strategy.valobs)

            indplots = strategy.valobs + indplots
            indsubplots = strategy.valobs + indsubplots

        props = font_manager.FontProperties(size=self.params.scheme.subtxtsize)
        axis = list()

        # if "dates" are passed, matploblib adds non-existing dates (ie weekends) creating gaps
        # passing only the index number and combined with a formatter, only those are needed
        dt = strategy._clock.datetime.plot()
        rdt = range(len(strategy._clock.datetime))

        numvols = 0
        for row, data in enumerate(strategy.datas):
            if not row:
                axdata = pyplot.subplot2grid((nrows, 1), (row, 0), rowspan=self.params.scheme.rowsmajor)
            else:
                axdata = pyplot.subplot2grid((nrows, 1), (self.params.scheme.rowsmajor + row + numvols, 0),
                                             rowspan=self.params.scheme.rowsminor, sharex=axis[0])
            axis.append(axdata)
            closes = data.close.plot()
            opens = data.open.plot()
            if self.params.scheme.style.startswith('line'):
                axdata.plot(rdt, closes, aa=True, label='_nolegend_')
            else:
                highs = data.high.plot()
                lows = data.low.plot()
                if self.params.scheme.style.startswith('candle'):
                    candlestick2_ohlc(axdata, opens, highs, lows, closes, width=1.0,
                                      colorup=self.params.scheme.barup, colordown=self.params.scheme.bardown,
                                      alpha=self.params.scheme.bartrans)
                elif self.params.scheme.style.startswith('bar') or True:
                    # final default option
                    plot_day_summary2_ohlc(axdata, opens, highs, lows, closes, ticksize=4,
                                           colorup=self.params.scheme.barup,
                                           colordown=self.params.scheme.bardown)

            axdata.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(prune='upper'))

            ops = strategy.dataops[data]
            axdata.plot(rdt, ops.buy.plot(),
                        color=self.params.scheme.buycolor,
                        marker=self.params.scheme.buymarker,
                        markersize=self.params.scheme.buymarkersize,
                        ls='-',
                        fillstyle='none',
                        label=self.params.scheme.buylabel)
            axdata.plot(rdt, ops.sell.plot(),
                        color=self.params.scheme.sellcolor,
                        marker=self.params.scheme.sellmarker,
                        markersize=self.params.scheme.sellmarkersize,
                        fillstyle='none',
                        label=self.params.scheme.selllabel)

            if self.params.scheme.volume:
                volumes = data.volume.plot()
                if max(volumes):
                    if self.params.scheme.voloverlay:
                        # Push the data upwards
                        bot, top = axdata.get_ylim()
                        axdata.set_ylim(bot * self.params.scheme.volover_bot, top)

                        # Clone the data ax
                        axvol = axdata.twinx()
                    else:
                        # Create independent subplot
                        volrow = self.params.scheme.rowsmajor + row + numvols
                        axvol = pyplot.subplot2grid((nrows, 1), (volrow, 0),
                                                    rowspan=self.params.scheme.rowsminor, sharex=axis[0])
                        numvols += 1
                        axis.append(axvol)

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
                        axvol.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(prune='upper'))

            # Make room for the labels at the top
            bot, top = axdata.get_ylim()
            axdata.set_ylim(bot, top * 1.03)

        for ind in indplots:
            indplotinfo = getattr(ind, 'plotinfo', dict())
            if ind.subplot:
                axind = pyplot.subplot2grid((nrows, 1), (self.params.scheme.rowsmajor + row + numvols, 0),
                                            rowspan=self.params.scheme.rowsminor, sharex=axis[0])
                row += 1
                axis.append(axind)
            elif ind._clock in strategy.datas:
                axind = axis[strategy.datas.index(ind._clock)]
            else: # must be another indicator
                idx = dataslen + numvols + indsubplots.index(ind._clock)
                axind = axis[idx]

            indlabel = ind.plotlabel()
            for lineidx in xrange(ind.size()):
                line = ind.lines[lineidx]
                linealias = ind.lines._getlinealias(lineidx)

                lineplotinfo = indplotinfo.get(linealias, dict())
                plotlines = lineplotinfo

                if ind.subplot:
                    # plotting on own subplot
                    if lineplotinfo.pop('_plotskip', False):
                        label = '_nolegend'
                    elif ind.size() == 1:
                        if self.params.scheme.skipmainsinglelabels:
                            label = '_nolegend'
                        elif not indplotinfo.get('_plotsinglelines', False):
                            label = '_nolegend'
                        else:
                            label = linealias
                    else:
                        label = linealias
                else:
                    # plotting on someone else's ... indicator label to be shown
                    label = '_nolegend' if lineidx else indlabel

                pltmethod = getattr(axind, lineplotinfo.get('_method', 'plot'))
                plotkwargs = dict(aa=True, label=label, **lineplotinfo)
                plotkwargs.pop('_method', None) # avoid passing an unknown parameter
                if ind.subplot:
                    plotkwargs['color'] = self.params.scheme.lines[lineidx]

                pltmethod(rdt, line.plot(), **plotkwargs)

            if ind.subplot:
                axind.text(0.005, 0.97, indlabel, va='top', transform=axind.transAxes,
                           alpha=self.params.scheme.subtxttrans, fontsize=self.params.scheme.subtxtsize)

        # Go over the indicator subplots to put the legend in place
        # if done before ... indicators over indicators (ex: movavg on rsi) will not show
        # up in the legend, because such indicator is seen later in the previous loop
        for indidx, ind in enumerate(indsubplots):
            axind = axis[dataslen + numvols + indidx]

            # Let's do the ticks here in case they are automatic and an indicator on indicator
            # adds a bit to the automatic y scaling
            yticks = getattr(ind, 'plotticks', None)
            if yticks:
                axind.set_yticks(yticks)
            else:
                axind.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=4, prune='upper'))

            # This can be done also in the previous loop ... but since we do the ticks here
            hlines = getattr(ind, 'plothlines', [])
            for hline in hlines:
                axind.axhline(hline,
                              color=self.params.scheme.hlinescolor,
                              ls=self.params.scheme.hlinesstyle,
                              lw=self.params.scheme.hlineswidth)

            if self.params.scheme.legendind and getattr(ind, 'plotlegend', True):
                handles, labels = axind.get_legend_handles_labels()
                # Ensure that we have something to show
                if labels:
                    # Legend must be done here to ensure legend includes lines from ind on ind
                    legend = axind.legend(loc=self.params.scheme.legendindloc,
                                          shadow=False, fancybox=True, prop=props)
                    if legend:
                        legend.get_frame().set_alpha(0.25)

        for dataidx in xrange(dataslen):
            ax = axis[dataidx]
            legend = axdata.legend(
                loc='upper center', shadow=False, fancybox=False, prop=props, numpoints=1, ncol=10)
            if legend:
                legend.get_frame().set_alpha(self.params.scheme.legendtrans)

        for ax in axis:
            ax.grid(True)

        axis[-1].xaxis.set_major_formatter(MyFormatter(dt))
        axis[-1].xaxis.set_minor_formatter(MyFormatter2(dt))

        fig.subplots_adjust(hspace=self.params.scheme.plotdist, top=0.98, left=0.05, bottom=0.00, right=0.95)
        fig.autofmt_xdate()
        pyplot.autoscale(axis='x', tight=True)

    def show(self):
        pyplot.show()


class MyFormatter(matplotlib.ticker.Formatter):
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


class MyFormatter2(matplotlib.ticker.Formatter):
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
