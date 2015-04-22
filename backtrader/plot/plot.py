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
import math

import six
from six.moves import xrange

import matplotlib.dates as mdates
import matplotlib.pyplot as mpyplot
import matplotlib.ticker as mticker
import matplotlib.font_manager as mfontmgr
import matplotlib.finance as mfinance

from .. import MetaParams
from .. import TimeFrame

from .finance import plot_candlestick, plot_ohlc, plot_volume, plot_lineonclose
from .formatters import (MyVolFormatter, MyDateFormatter)
from .scheme import PlotScheme
from .utils import tag_box_style


class PInfo(object):
    def __init__(self, sch):
        self.sch = sch
        self.nrows = 0
        self.row = 0
        self.x = None
        self.xlen = 0
        self.sharex = None
        self.daxis = collections.OrderedDict()
        self.coloridx = collections.defaultdict(lambda: -1)

    def nextcolor(self, ax):
        self.coloridx[ax] += 1
        return self.coloridx[ax]

    def color(self, ax):
        return self.sch.color(self.coloridx[ax])


class Plot(six.with_metaclass(MetaParams, object)):
    params = (('scheme', PlotScheme()),)

    def __init__(self, **kwargs):
        for pname, pvalue in kwargs.items():
            setattr(self.p.scheme, pname, pvalue)

    def drawtag(self, ax, x, y, facecolor, edgecolor, alpha=0.9, **kwargs):

        txt = ax.text(x, y, '%.2f' % y, va='center', ha='left',
                      fontsize=self.pinf.sch.subtxtsize,
                      bbox=dict(boxstyle=tag_box_style,
                                facecolor=facecolor,
                                edgecolor=edgecolor,
                                alpha=alpha),
                      **kwargs)

    def plot(self, strategy):
        if not strategy.datas:
            return

        self.pinf = PInfo(self.p.scheme)
        self.pinf.prop = mfontmgr.FontProperties(size=self.pinf.sch.subtxtsize)
        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        # prepare a figure
        fig = mpyplot.figure(0)

        # Do the plotting
        # Things that go always at the top (observers)
        for ptop in self.dplotstop:
            self.plotind(ptop, self.dplotsover[ptop])

        # Create the rest on a per data basis
        for data in strategy.datas:
            for ind in self.dplotsup[data]:
                self.plotind(ind, self.dplotsover[ind])

            self.plotdata(data, self.dplotsover[data])

            for ind in self.dplotsdown[data]:
                self.plotind(ind, self.dplotsover[ind])

        lastax = self.pinf.daxis.values()[-1]
        # Date formatting for the x axis - only the last one needs it
        if True:
            locator = mticker.AutoLocator()
            lastax.xaxis.set_major_locator(locator)
            lastax.xaxis.set_major_formatter(MyDateFormatter(self.pinf.xreal))
        elif False:
            # locator, formatter = getlocator(self.pinf.xreal)
            lastax.xaxis.set_major_locator(locator)
            lastax.xaxis.set_major_formatter(formatter)

        # Put the subplots as indicated by hspace (0 is touching each other)
        fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                            top=0.98, left=0.05, bottom=0.05, right=0.95)

        # Applying fig.autofmt_xdate if the data axis is the last one
        # breaks the presentation of the date labels. why?
        # Applying the manual rotation with setp cures the problem
        # but the labels from all axis but the last have to be hidden
        # fig.autofmt_xdate(bottom=0.25, rotation=15)

        for ax in self.pinf.daxis.values():
            mpyplot.setp(ax.get_xticklabels(), visible=False)
        mpyplot.setp(lastax.get_xticklabels(), visible=True, rotation=15)
        # mpyplot.setp(mpyplot.xticks()[1], rotation=15)

        # Things must be tight along the x axis (to fill both ends)
        mpyplot.autoscale(axis='x', tight=True)

    def calcrows(self, strategy):
        # Calculate the total number of rows
        rowsmajor = self.pinf.sch.rowsmajor
        rowsminor = self.pinf.sch.rowsminor
        nrows = 0

        # Datas and volumes
        nrows += len(strategy.datas) * rowsmajor
        if self.pinf.sch.volume and not self.pinf.sch.voloverlay:
            nrows += len(strategy.datas) * rowsminor

        # top indicators/observers
        nrows += len(self.dplotstop) * rowsminor

        # indicators above datas
        nrows += sum(len(v) for v in self.dplotsup.values())
        nrows += sum(len(v) for v in self.dplotsdown.values())

        self.pinf.nrows = nrows
        self.pinf.xreal = strategy._clock.datetime.plot()
        self.pinf.xlen = len(self.pinf.xreal)
        self.pinf.x = list(xrange(self.pinf.xlen))

    def newaxis(self, obj, rowspan):
        ax = mpyplot.subplot2grid((self.pinf.nrows, 1), (self.pinf.row, 0),
                                  rowspan=rowspan, sharex=self.pinf.sharex)

        # update the sharex information if not available
        if self.pinf.sharex is None:
            self.pinf.sharex = ax

        # update the row index with the taken rows
        self.pinf.row += rowspan

        # save the mapping indicator - axis and return
        self.pinf.daxis[obj] = ax

        # Activate grid in all axes if requested
        ax.yaxis.tick_right()
        ax.grid(self.pinf.sch.grid)

        return ax

    def plotind(self, ind, subinds=None, masterax=None):
        sch = self.p.scheme

        # check subind
        subinds = subinds or []

        # Get an axis for this plot
        ax = masterax or self.newaxis(ind, rowspan=self.pinf.sch.rowsminor)

        indlabel = ind.plotlabel()

        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)
            lineplotinfo = getattr(ind.plotlines, linealias)

            if lineplotinfo._get('_plotskip', False):
                continue

            # Legend label only when plotting 1st line
            if masterax and not ind.plotinfo.plotlinelabels:
                label = indlabel * (lineidx == 0) or '_nolegend'
            else:
                label = linealias

            # plot data
            lplot = line.plot()

            if not math.isnan(lplot[-1]):
                label += ' %.2f' % lplot[-1]

            plotkwargs = dict()
            linekwargs = lineplotinfo._getkwargs(skip_=True)

            if linekwargs.get('color', None) is None:
                if not lineplotinfo._get('_samecolor', False):
                    self.pinf.nextcolor(ax)
                plotkwargs['color'] = self.pinf.color(ax)

            plotkwargs.update(dict(aa=True, label=label))
            plotkwargs.update(**linekwargs)

            pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))
            plottedline = pltmethod(self.pinf.x, lplot, **plotkwargs)
            try:
                plottedline = plottedline[0]
            except:
                # Possibly a container of artists (when plotting bars)
                pass

            if not math.isnan(lplot[-1]):
                # line has valid values, plot a tag for the last value
                self.drawtag(ax, self.pinf.xlen, lplot[-1],
                             facecolor='white',
                             edgecolor=self.pinf.color(ax))

        # plot subindicators that were created on self
        for subind in subinds:
            self.plotind(subind, subinds=self.dplotsover[subind], masterax=ax)

        if not masterax:
            # Set specific or generic ticks
            yticks = ind.plotinfo._get('plotyticks', None)
            if yticks is not None:
                ax.set_yticks(yticks)
            else:
                locator = mticker.MaxNLocator(nbins=4, prune='both')
                ax.yaxis.set_major_locator(locator)

            # Set specific hlines if asked to
            for hline in ind.plotinfo._get('plothlines', []):
                ax.axhline(hline, color=self.pinf.sch.hlinescolor,
                           ls=self.pinf.sch.hlinesstyle,
                           lw=self.pinf.sch.hlineswidth)

            if self.pinf.sch.legendind and \
               ind.plotinfo._get('plotlegend', True):

                handles, labels = ax.get_legend_handles_labels()
                # Ensure that we have something to show
                if labels:
                    # Legend done here to ensure it includes all plots
                    legend = ax.legend(loc=self.pinf.sch.legendindloc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

                    legend.set_title(indlabel, prop=self.pinf.prop)
                    # hack: if title is set. legend has a Vbox for the labels
                    # which has a default "center" set
                    legend._legend_box.align = 'left'

    def plotdata(self, data, indicators):
        ax = self.newaxis(data, rowspan=self.pinf.sch.rowsmajor)

        closes = data.close.plot()
        opens = data.open.plot()
        highs = data.high.plot()
        lows = data.low.plot()

        datalabel = ''
        dataname = ''
        if hasattr(data, '_name') and data._name:
            datalabel += data._name

        if hasattr(data, '_compression') and \
           hasattr(data, '_timeframe'):
            tfname = TimeFrame.getname(data._timeframe, data._compression)
            datalabel += ' (%d %s)' % (data._compression, tfname)

            if False:
                fromdate = data._daterange[0]
                todate = data._daterange[1]
                if fromdate is not None or todate is not None:
                    datatitle += ' ('
                    fmtstr = '%Y-%m-%d'
                    if data._timeframe == TimeFrame.Minutes:
                        fmtstr += ' %H%M'

                    if fromdate is not None:
                        datatitle += fromdate.strftime(fmtstr)

                    datatitle += ' - '

                    if todate is not None:
                        datatitle += todate.strftime(fmtstr)

                    datatitle += ')'

        datalabel += ' O:%.2f H:%2.f L:%.2f C:%.2f' % \
                     (opens[-1], highs[-1], lows[-1], closes[-1])

        if self.pinf.sch.style.startswith('line'):
            plottedline, = plot_lineonclose(
                ax, self.pinf.x, closes,
                color=self.pinf.sch.loc, label=datalabel)
        else:
            if self.pinf.sch.style.startswith('candle'):
                plot_candlestick(
                    ax, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel)

            elif self.pinf.sch.style.startswith('bar') or True:
                # final default option -- should be "else"
                plot_ohlc(
                    ax, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel)

        # Code to place a label at the right hand side with the last value
        self.drawtag(ax, self.pinf.xlen, closes[-1],
                     facecolor='white', edgecolor=self.pinf.sch.loc)

        ax.yaxis.set_major_locator(mticker.MaxNLocator(prune='both'))
        ax.set_ylim(ax.get_ylim())

        if self.pinf.sch.volume:
            # volume plot data
            volumes = data.volume.plot()

            # Get the plotting axis
            if self.pinf.sch.voloverlay:
                axvol = ax
                volalpha = self.pinf.sch.voltrans
            else:
                axvol = self.newaxis(data.volume,
                                     rowspan=self.pinf.sch.rowsminor)
                volalpha = 1.0

            # Plot the volume (no matter if as overlay or standalone)
            vollabel = 'Volume'
            bc, = plot_volume(axvol, opens, closes, volumes,
                              colorup=self.pinf.sch.volup,
                              colordown=self.pinf.sch.voldown,
                              overlay=self.pinf.sch.voloverlay,
                              overscaling=self.pinf.sch.volscaling,
                              overpushup=self.pinf.sch.volpushup,
                              alpha=volalpha,
                              label=vollabel)

            nbins = 6
            prune = 'both'
            maxvol = volylim = max(volumes)
            if self.pinf.sch.voloverlay:
                axvol = axvol.twinx()
                # store for a potential plot over it
                # self.pinf.daxis[data.volume] = axvol

                nbins = int(nbins / self.pinf.sch.volscaling)
                prune = None

                axvol.yaxis.tick_left()
                # twinx pushes original yaxis to the left - correct it
                ax.yaxis.tick_right()

                volylim /= self.pinf.sch.volscaling
                # axvol.set_ylim(0, volylim, auto=True)
                # mpyplot.autoscale is called with axis='x' we need
                # not updating the datalimits even. But if axis='both'
                # autoscale is tightening ylim = ydatalim and given
                # not data is plotted to the axis, we'd need to manually
                # update the data limit with the 3 following lines
                vlimits = (0.0, self.pinf.xlen), (0.0, volylim)
                axvol.update_datalim(vlimits)
                axvol.autoscale_view()  # not needed

            locator = mticker.MaxNLocator(nbins=nbins, prune=prune)
            axvol.yaxis.set_major_locator(locator)
            axvol.yaxis.set_major_formatter(MyVolFormatter(maxvol))

        for ind in indicators:
            self.plotind(ind, subinds=self.dplotsover[ind], masterax=ax)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            # put data and volume legend entries in the 1st positions
            # because they are "collections" they are considered after Line2D
            # for the legend entries, which is not our desire
            if self.pinf.sch.volume and self.pinf.sch.voloverlay:
                vidx = labels.index(vollabel)
                labels.insert(0, labels.pop(vidx))
                handles.insert(0, handles.pop(vidx))

            didx = labels.index(datalabel)
            labels.insert(0, labels.pop(didx))
            handles.insert(0, handles.pop(didx))

            # feed handles/labels to legend to get right order
            legend = ax.legend(handles, labels,
                               loc='upper left', frameon=False, shadow=False,
                               fancybox=False,
                               prop=self.pinf.prop, numpoints=1, ncol=1)

            # hack: if title is set. legend has a Vbox for the labels
            # which has a default "center" set
            legend._legend_box.align = 'left'

    def show(self):
        mpyplot.show()

    def sortdataindicators(self, strategy):
        # These lists/dictionaries hold the subplots that go above each data
        self.dplotstop = list()
        self.dplotsup = collections.defaultdict(list)
        self.dplotsdown = collections.defaultdict(list)
        self.dplotsover = collections.defaultdict(list)

        # Sort observers in the different lists/dictionaries
        for x in strategy.getobservers():
            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            if x.plotinfo.subplot:
                self.dplotstop.append(x)
            else:
                key = getattr(x._clock, 'owner', x._clock)
                self.dplotsover[key].append(x)

        # Sort indicators in the different lists/dictionaries
        for x in strategy.getindicators():
            if not hasattr(x, 'plotinfo'):
                # no plotting support - so far LineSingle derived classes
                continue

            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            key = getattr(x._clock, 'owner', x._clock)
            if x.plotinfo.subplot:
                # support LineSeriesStub which has "owner" to point to the data
                if x.plotinfo.plotabove:
                    self.dplotsup[key].append(x)
                else:
                    self.dplotsdown[key].append(x)
            else:
                self.dplotsover[key].append(x)
