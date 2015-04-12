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

import collections
import math

import six
from six.moves import xrange

try:
    import matplotlib
    from matplotlib import pyplot
    import matplotlib.ticker
    from matplotlib.finance import volume_overlay, volume_overlay2, plot_day_summary2_ohlc, candlestick2_ohlc
    import matplotlib.font_manager as font_manager
    import numpy as np
except ImportError:
    matploblib = None

from .metabase import MetaParams
from . import TimeFrame


class PlotScheme(object):
    volume = True
    voloverlay = True
    volover_top = 3.0
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
    voltrans = 0.2

    subtxttrans = 0.66
    subtxtsize = 9

    legendtrans = 0.25
    legendind = True
    legendindloc = 'upper left'

    hlinescolor = '0.66' # shade of gray
    hlinesstyle = '--'
    hlineswidth = 1.0

    lcolors = ['black', 'tomato', 'blue', 'green', 'brown', 'magenta', 'cyan', 'gold',]


class PInfo(object):
    def __init__(self):
        self.nrows = 0
        self.row = 0
        self.x = None
        self.xlen = 0
        self.sharex = None
        self.daxis = collections.OrderedDict()
        self.plotstatus = dict()


class Plot(six.with_metaclass(MetaParams, object)):

    params = (('scheme', PlotScheme()),)

    def __init__(self, **kwargs):
        if not matplotlib:
            raise ImportError('Please install matplotlib in order to enable plotting')

        for pname, pvalue in kwargs.items():
            setattr(self.p.scheme, pname, pvalue)

    def plot(self, strategy):
        if not strategy.datas:
            return

        sch = self.p.scheme

        # These lists/dictionaries hold the subplots that go above each data
        self.dplotstop = list()
        self.dplotsup = collections.defaultdict(list)
        self.dplotsdown = collections.defaultdict(list)
        self.dplotson = collections.defaultdict(list)

        # Sort observers in the different lists/dictionaries
        for x in strategy.getobservers():
            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            if x.plotinfo.subplot:
                self.dplotstop.append(x)
            else:
                key = getattr(x._clock, 'owner', x._clock)
                self.dplotson[key].append(x)

        # Sort indicators in the different lists/dictionaries
        for x in strategy.getindicators():
            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            key = getattr(x._clock, 'owner', x._clock)
            if x.plotinfo.subplot:
                # support LineSeriesStub which features an "owner" to point to the data
                if x.plotinfo.plotabove:
                    self.dplotsup[key].append(x)
                else:
                    self.dplotsdown[key].append(x)
            else:
                self.dplotson[key].append(x)

        # Calculate the total number of rows
        rowsmajor = sch.rowsmajor
        rowsminor = sch.rowsminor
        nrows = 0

        # Datas and volumes
        nrows += len(strategy.datas) * rowsmajor
        if sch.volume and not sch.voloverlay:
            nrows += len(strategy.datas) * rowsminor

        # top indicators/observers
        nrows += len(self.dplotstop) * rowsminor

        # indicators above datas
        nrows += sum(len(v) for v in self.dplotsup.values())
        nrows += sum(len(v) for v in self.dplotsdown.values())

        pinfo = PInfo()
        pinfo.nrows = nrows
        pinfo.xreal = strategy._clock.datetime.plot()
        pinfo.xlen = len(pinfo.xreal)
        pinfo.x = list(xrange(pinfo.xlen))

        fig = pyplot.figure(0)

        # Do the plotting
        # Things that go always at the top (observers)
        for ptop in self.dplotstop:
            self.plotind(pinfo, ptop, self.dplotson[ptop])

        # Create the rest on a per data basis
        for data in strategy.datas:
            for ind in self.dplotsup[data]:
                self.plotind(pinfo, ind, self.dplotson[ind])

            self.plotdata(pinfo, data, self.dplotson[data])

            for ind in self.dplotsdown[data]:
                self.plotind(pinfo, ind, self.dplotson[ind])

        # Date formatting for the x axis - only the last one needs it
        lastax = pinfo.daxis.values()[-1]
        lastax.xaxis.set_major_formatter(MyDateFormatter(pinfo.xreal))
        lastax.xaxis.set_minor_formatter(MyDateFormatter2(pinfo.xreal))

        # Put the subplots as indicated by hspace (0 is touching each other)
        fig.subplots_adjust(hspace=sch.plotdist, top=0.98, left=0.05, bottom=0.00, right=0.95)
        fig.autofmt_xdate(bottom=0.05, rotation=15)

        # Things must be tight along the x axis (to fill both ends)
        pyplot.autoscale(axis='x', tight=True)
        pyplot.autoscale(tight=True)

    def newaxis(self, pinfo, obj, rowspan):
        sch = self.p.scheme

        ax = pyplot.subplot2grid((pinfo.nrows, 1),(pinfo.row, 0), rowspan=rowspan, sharex=pinfo.sharex)

        # update the sharex information if not available
        if pinfo.sharex is None:
            pinfo.sharex = ax

        # update the row index with the taken rows
        pinfo.row += rowspan

        # save the mapping indicator - axis and return
        pinfo.daxis[obj] = ax

        # Activate grid in all axes if requested
        ax.yaxis.tick_right()
        ax.grid(sch.grid)

        # Save a default plotstatus for ax (lzorder, tzorder, coloridx)
        pinfo.plotstatus[ax] = (0, 0, 0)

        return ax

    def plotind(self, pinfo, ind, subinds=None, masterax=None):
        props = font_manager.FontProperties(size=self.params.scheme.subtxtsize)
        sch = self.p.scheme

        # check subind
        subinds = subinds or []

        # Get an axis for this plot
        ax = masterax or self.newaxis(pinfo, ind, rowspan=sch.rowsminor)

        # preset some values
        lzorder, tzorder, coloridx = pinfo.plotstatus[ax]

        indlabel = ind.plotlabel()

        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)
            lineplotinfo = getattr(ind.plotlines, linealias)

            if lineplotinfo._get('_plotskip', False):
                continue

            # Legend label only when plotting 1st line
            if masterax:
                label = indlabel * (lineidx == 0) or '_nolegend'
            else:
                label = linealias

            # plot data
            lplot = line.plot()

            if not math.isnan(lplot[-1]):
                label += ' %.2f' % lplot[-1]

            plotkwargs = dict()

            if not lineplotinfo._get('_samecolor', False):
                coloridx = (coloridx + 1) % len(sch.lcolors)

            plotkwargs['color'] = sch.lcolors[coloridx]

            plotkwargs.update(dict(aa=True, label=label))
            plotkwargs.update(**lineplotinfo._getkwargs(skip_=True))
            if lzorder:
                plotkwargs['zorder'] = lzorder * 0.995

            pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))
            plottedline = pltmethod(pinfo.x, lplot, **plotkwargs)
            try:
                plottedline = plottedline[0]
            except:
                # Possibly a container of artists (when plotting bars)
                pass
            lzorder = plottedline.get_zorder()

            if not math.isnan(lplot[-1]):
                # if line has produced values ... plot a tag for the last value
                tagkwargs = dict()
                if tzorder:
                    tagkwargs['zorder'] = tzorder * 0.995
                tzorder = drawtag(ax, pinfo.xlen, lplot[-1], edgecolor=sch.lcolors[coloridx],
                                  fontsize=sch.subtxtsize, **tagkwargs)

        pinfo.plotstatus[ax] = (lzorder, tzorder, coloridx)

        # plot subindicators that were created on self
        for subind in subinds:
            self.plotind(pinfo, subind, subinds=self.dplotson[subind], masterax=ax)

        if not masterax:
            # Set specific or generic ticks
            yticks = ind.plotinfo._get('yticks', None)
            if yticks is not None:
                ax.set_yticks(yticks)
            else:
                ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=4, prune='both'))

            # Set specific hlines if asked to
            hlines = ind.plotinfo._get('hlines', [])
            lzorder, _, _ = pinfo.plotstatus[ax]
            for hline in hlines:
                lzorder *= 0.995
                ax.axhline(hline, color=sch.hlinescolor, ls=sch.hlinesstyle, lw=sch.hlineswidth, zorder=lzorder,
                )

            pinfo.plotstatus[ax] = (lzorder, tzorder, coloridx)

            if sch.legendind and ind.plotinfo._get('legend', True):
                handles, labels = ax.get_legend_handles_labels()
                # Ensure that we have something to show
                if labels:
                    # Legend must be done here to ensure legend includes lines from ind on ind
                    legend = ax.legend(loc=sch.legendindloc, numpoints=1,
                                       frameon=False, shadow=False, fancybox=False, fontsize=sch.subtxtsize)

                    legend.set_title(indlabel, prop=props)
                    if legend:
                        # legend.get_frame().set_alpha(sch.legendtrans)
                        # hack if title is set, because the _legend_box (a VPacker) has "center" as default
                        legend._legend_box.align='left'


    def plotdata(self, pinfo, data, indicators):
        sch = self.p.scheme
        props = font_manager.FontProperties(size=sch.subtxtsize)

        # if "dates" are passed, matploblib adds non-existing dates (ie weekends) creating gaps
        # passing only the index number and combined with a formatter, only those are needed
        ax = self.newaxis(pinfo, data, rowspan=sch.rowsmajor)

        closes = data.close.plot()
        opens = data.open.plot()

        datalabel = ''
        if hasattr(data, '_name') and data._name:
            datalabel += data._name
            datalabel += ' (%d %s)' % (data._compression, TimeFrame.getname(data._timeframe, data._compression))

            if False:
                fromdate = data._daterange[0]
                todate = data._daterange[1]
                if fromdate is not None or todate is not None:
                    datalabel += ' ('
                    fmtstr = '%Y-%m-%d'
                    if data._timeframe == TimeFrame.Minutes:
                        fmtstr += ' %H%M'

                    if fromdate is not None:
                        datalabel += fromdate.strftime(fmtstr)

                    datalabel += ' - '

                    if todate is not None:
                        datalabel += todate.strftime(fmtstr)

                    datalabel += ')'

        if sch.style.startswith('line'):
            datalabel += ' C: %.2f' % closes[-1]
            plottedline, = ax.plot(pinfo.x, closes, aa=True, label=datalabel, color=sch.lcolors[0])

        else:
            highs = data.high.plot()
            lows = data.low.plot()

            datalabel += ' O:%.2f H:%2.f L:%.2f C:%.2f' % (opens[-1], highs[-1], lows[-1], closes[-1])

            if sch.style.startswith('candle'):
                coll = candlestick2_ohlc(ax, opens, highs, lows, closes, width=1.0,
                                       colorup=sch.barup,
                                       colordown=sch.bardown,
                                       alpha=sch.bartrans)
            elif sch.style.startswith('bar') or True:
                # final default option -- should be "else"
                 coll = plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize=4,
                                               colorup=sch.barup,
                                               colordown=sch.bardown)

        # Code to place a label at the right hand side withthe last value
        datazorder = drawtag(ax, pinfo.xlen, closes[-1], edgecolor=sch.lcolors[0], fontsize=sch.subtxtsize)

        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(prune='both'))

        if sch.volume:
            volumes = data.volume.plot()
            # Do only plot if a volume actually exists
            # This could be done in advance to actually tighten the chart if some data has no volume
            maxvol = max(volumes)
            if maxvol:
                if self.params.scheme.voloverlay:
                    axvol = ax.twinx()
                else:
                    # Create independent subplot
                    axvol = self.newaxis(pinfo, data.volume, rowspan=sch.rowsmajor)

                axvol.yaxis.set_major_formatter(MyVolFormatter(maxvol))

                # Plot the volume (no matter if as overlay or standalone)
                volalpha = 1.0 if not sch.voloverlay else sch.voltrans
                if True:
                    bc = volume_overlay(axvol, opens, closes, volumes,
                                        colorup=sch.volup,
                                        colordown=sch.voldown,
                                        alpha=volalpha, width=1)
                else:
                    bc = volume_overlay2(axvol, closes, volumes,
                                         colorup=sch.volup,
                                         colordown=sch.voldown,
                                         alpha=volalpha, width=1)

                if sch.voloverlay:
                    # Keep it at the bottom
                    axvol.yaxis.tick_left()
                    # put the data to the other side possible bug in matplotlib, because twin should not affect
                    # master
                    ax.yaxis.tick_right()
                    # limit the volume overlay plot to the bottom by increasing the vertical scale
                    # several times over the max
                    bot, top = axvol.get_ylim()
                    axvol.set_ylim(bot, top * sch.volover_top)
                    # Alternative is to calculate "ticks" based on max volume and set them
                    nbins = 10
                    prune = None
                else:
                    nbins = 6
                    prune = 'both'
                    # Cut the top of the y axis ticks
                axvol.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=nbins, prune=prune))


        # Setting ylim to the value set by "data" ensures that indicators plotted on the data
        # will not modify the scale of the y axis
        ax.set_ylim(ax.get_ylim())

        # Manual status update with default values after plotting the data 2.0 for lines, 3.0 for text
        # and current color is 1
        pinfo.plotstatus[ax] = (2.0, 3.0, 1)

        for ind in indicators:
            self.plotind(pinfo, ind, subinds=self.dplotson[ind], masterax=ax)

        # NOTE: Plot Indicators/Observers before setting the legend of the "datas"
        # because some indicators will insert labes into the data legends

        # Data legends
        legend = ax.legend(
            loc='upper left', frameon=False, shadow=False, fancybox=False, prop=props, numpoints=1, ncol=1)
        if legend:
            # legend.get_frame().set_alpha(sch.legendtrans)
            # hack if title is set, because the _legend_box (a VPacker) has "center" as default
            legend._legend_box.align='left'

    def show(self):
        pyplot.show()


class MyVolFormatter(matplotlib.ticker.Formatter):
    Suffixes = ['', 'K', 'M', 'G', 'T', 'P']

    def __init__(self, volmax):
        self.volmax = volmax
        magnitude = 0
        self.divisor = 1.0
        while abs(volmax / self.divisor) >= 1000:
            magnitude += 1
            self.divisor *= 1000.0

        self.suffix = self.Suffixes[magnitude]

    def __call__(self, y, pos=0):
        '''Return the label for time x at position pos'''

        if y > self.volmax * 1.20:
            return ''

        y = int(y / self.divisor)
        return '%d%s' % (y, self.suffix)


class MyDateFormatter(matplotlib.ticker.Formatter):
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


class MyDateFormatter2(matplotlib.ticker.Formatter):
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

def drawtag(ax, x, y, edgecolor, fontsize,  alpha=0.9, **kwargs):
    txt = ax.text(x, y,
                  '%.2f' % y,
                  va='center',
                  ha='left',
                  fontsize=fontsize,
                  bbox=dict(boxstyle=custom_box_style,
                            facecolor='white',
                            edgecolor=edgecolor,
                            alpha=alpha),
                  **kwargs)
    return txt.get_zorder()


def custom_box_style(x0, y0, width, height, mutation_size, mutation_aspect=1):
    """
    Given the location and size of the box, return the path of
    the box around it.

     - *x0*, *y0*, *width*, *height* : location and size of the box
     - *mutation_size* : a reference scale for the mutation.
     - *aspect_ratio* : aspect-ration for the mutation.
    """

    # note that we are ignoring mutation_aspect. This is okay in general.

    # padding
    from matplotlib.path import Path

    mypad = 0.2
    pad = mutation_size * mypad

    # width and height with padding added.
    width, height = width + 2.*pad, height + 2.*pad,

    # boundary of the padded box
    x0, y0 = x0-pad, y0-pad,
    x1, y1 = x0+width, y0 + height

    cp = [(x0, y0),
          (x1, y0), (x1, y1), (x0, y1),
          (x0-pad, (y0+y1)/2.), (x0, y0),
          (x0, y0)]

    com = [Path.MOVETO,
           Path.LINETO, Path.LINETO, Path.LINETO,
           Path.LINETO, Path.LINETO,
           Path.CLOSEPOLY]

    path = Path(cp, com)

    return path
