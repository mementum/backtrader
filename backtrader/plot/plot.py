#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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

import bisect
import collections

import math

from ..utils.py3 import range, with_metaclass

import matplotlib.dates as mdates
import matplotlib.font_manager as mfontmgr
import matplotlib.legend as mlegend
import matplotlib.pyplot as mpyplot
import matplotlib.ticker as mticker

from ..utils import OrderedDict

from .. import AutoInfoClass, MetaParams, TimeFrame

from .finance import plot_candlestick, plot_ohlc, plot_volume, plot_lineonclose
from .formatters import (MyVolFormatter, MyDateFormatter, getlocator)
from .scheme import PlotScheme
from .utils import tag_box_style
from .multicursor import MultiCursor


class PInfo(object):
    def __init__(self, sch):
        self.sch = sch
        self.nrows = 0
        self.row = 0
        self.clock = None
        self.x = None
        self.xlen = 0
        self.sharex = None
        self.figs = list()
        self.cursors = list()
        self.daxis = OrderedDict()
        self.ldaxis = list()
        self.zorder = dict()
        self.coloridx = collections.defaultdict(lambda: -1)

        self.prop = mfontmgr.FontProperties(size=self.sch.subtxtsize)

    def newfig(self, numfig):
        fig = mpyplot.figure(numfig)
        self.figs.append(fig)
        self.daxis = OrderedDict()
        self.ldaxis.append(self.daxis)
        self.row = 0
        self.sharex = None
        return fig

    def nextcolor(self, ax):
        self.coloridx[ax] += 1
        return self.coloridx[ax]

    def color(self, ax):
        return self.sch.color(self.coloridx[ax])

    def zordernext(self, ax):
        z = self.zorder[ax]
        if self.sch.zdown:
            return z * 0.9999
        return z * 1.0001

    def zordercur(self, ax):
        return self.zorder[ax]


class Plot(with_metaclass(MetaParams, object)):
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
                      # 3.0 is the minimum default for text
                      zorder=self.pinf.zorder[ax] + 3.0,
                      **kwargs)

    def plot(self, strategy, numfigs=1):
        if not strategy.datas:
            return

        self.pinf = PInfo(self.p.scheme)
        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        slen = len(strategy)
        d, m = divmod(slen, numfigs)
        pranges = list()
        for i in range(numfigs):
            a = d * i
            if i == (numfigs - 1):
                d += m  # add remainder to last stint
            b = a + d

            pranges.append([a, b, d])

        for numfig in range(numfigs):
            # prepare a figure
            fig = self.pinf.newfig(numfig)

            self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
            self.pinf.xstart = self.pinf.pstart
            self.pinf.xend = self.pinf.pend

            self.pinf.clock = strategy._clock
            self.pinf.xreal = strategy._clock.datetime.plot(
                self.pinf.pstart, self.pinf.psize)
            self.pinf.xlen = len(self.pinf.xreal)
            self.pinf.x = list(range(self.pinf.xlen))

            # Do the plotting
            # Things that go always at the top (observers)
            for ptop in self.dplotstop:
                self.plotind(ptop, subinds=self.dplotsover[ptop])

            # Create the rest on a per data basis
            for data in strategy.datas:
                for ind in self.dplotsup[data]:
                    self.plotind(
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

                self.plotdata(data, self.dplotsover[data])

                for ind in self.dplotsdown[data]:
                    self.plotind(
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

            cursor = MultiCursor(
                fig.canvas, list(self.pinf.daxis.values()),
                useblit=True,
                horizOn=True, vertOn=True,
                horizMulti=False, vertMulti=True,
                horizShared=True, vertShared=False,
                color='black', lw=1, ls=':')

            self.pinf.cursors.append(cursor)

            lastax = list(self.pinf.daxis.values())[-1]
            # Date formatting for the x axis - only the last one needs it
            if False:
                locator = mticker.AutoLocator()
                lastax.xaxis.set_major_locator(locator)
                # lastax.xaxis.set_major_formatter(MyDateFormatter(self.pinf.xreal))
                formatter = mdates.IndexDateFormatter(self.pinf.xreal,
                                                      fmt='%Y-%m-%d')
                lastax.xaxis.set_major_formatter(formatter)
            else:
                self.setlocators(strategy._clock)

            # Put the subplots as indicated by hspace
            fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                                top=0.98, left=0.05, bottom=0.05, right=0.95)

            # Applying fig.autofmt_xdate if the data axis is the last one
            # breaks the presentation of the date labels. why?
            # Applying the manual rotation with setp cures the problem
            # but the labels from all axis but the last have to be hidden
            if False:
                fig.autofmt_xdate(bottom=0.25, rotation=0)
            elif True:
                for ax in self.pinf.daxis.values():
                    mpyplot.setp(ax.get_xticklabels(), visible=False)
                    # ax.autoscale_view(tight=True)
                mpyplot.setp(lastax.get_xticklabels(),
                             visible=True,
                             rotation=self.pinf.sch.tickrotation)

            # Things must be tight along the x axis (to fill both ends)
            axtight = 'x' if not self.pinf.sch.ytight else 'both'
            mpyplot.autoscale(enable=True, axis=axtight, tight=True)

    def setlocators(self, data):
        ax = list(self.pinf.daxis.values())[-1]

        comp = getattr(data, '_compression', 1)
        tframe = getattr(data, '_timeframe', TimeFrame.Days)

        if tframe == TimeFrame.Years:
            fmtmajor = '%Y'
            fmtminor = '%Y'
            fmtdata = '%Y'
        elif tframe == TimeFrame.Months:
            fmtmajor = '%Y'
            fmtminor = '%b'
            fmtdata = '%Y-%m'
        elif tframe == TimeFrame.Weeks:
            fmtmajor = '%b'
            fmtminor = '%d'
            fmtdata = '%Y-%m-%d'
        elif tframe == TimeFrame.Days:
            fmtmajor = '%b'
            fmtminor = '%d'
            fmtdata = '%Y-%m-%d'
        elif tframe == TimeFrame.Minutes:
            fmtmajor = '%H:%M'
            fmtminor = '%H:%M'
            fmtdata = '%Y-%m-%d %H:%M'
        elif tframe == TimeFrame.Seconds:
            fmtmajor = '%M:%S'
            fmtminor = '%M:%S'
            fmtdata = '%M:%S'
        elif tframe == TimeFrame.MicroSeconds:
            fmtmajor = '%M:%S'
            fmtminor = '%S.%f'
            fmtdata = '%M:%S.%f'
        elif tframe == TimeFrame.Ticks:
            fmtmajor = '%M:%S'
            fmtminor = '%S.%f'
            fmtdata = '%M:%S.%f'

        fordata = MyDateFormatter(self.pinf.xreal, fmt=fmtdata)
        for dax in self.pinf.daxis.values():
            dax.fmt_xdata = fordata

        locmajor = mticker.AutoLocator()
        locminor = mticker.AutoMinorLocator()

        ax.xaxis.set_minor_locator(locminor)
        ax.xaxis.set_major_locator(locmajor)

        formajor = MyDateFormatter(self.pinf.xreal, fmt=fmtmajor)
        forminor = MyDateFormatter(self.pinf.xreal, fmt=fmtminor)
        ax.xaxis.set_major_formatter(formajor)
        ax.xaxis.set_minor_formatter(forminor)

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
        ax.grid(self.pinf.sch.grid, which='both')

        return ax

    def plotind(self, ind,
                subinds=None, upinds=None, downinds=None,
                masterax=None):

        sch = self.p.scheme

        # check subind
        subinds = subinds or []
        upinds = upinds or []
        downinds = downinds or []

        # plot subindicators on self with independent axis above
        for upind in upinds:
            self.plotind(upind)

        # Get an axis for this plot
        ax = masterax or self.newaxis(ind, rowspan=self.pinf.sch.rowsminor)

        indlabel = ind.plotlabel()

        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)

            lineplotinfo = getattr(ind.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(ind.plotlines, linealias, None)

            if not lineplotinfo:
                lineplotinfo = AutoInfoClass()

            if lineplotinfo._get('_plotskip', False):
                continue

            # Legend label only when plotting 1st line
            if masterax and not ind.plotinfo.plotlinelabels:
                label = indlabel * (lineidx == 0) or '_nolegend'
            else:
                label = lineplotinfo._get('_name', '') or linealias

            # plot data
            lplot = line.plotrange(self.pinf.xstart, self.pinf.xend)

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

            if ax in self.pinf.zorder:
                plotkwargs['zorder'] = self.pinf.zordernext(ax)

            if ind.plotinfo.plotmaster is not None:
                clk = getattr(ind._clock, 'owner', ind._clock)
                mlens = getattr(clk, 'mlen', None)
                newlplot = list()
                if mlens:
                    prevmlen = 0
                    for i, mlen in enumerate(mlens):
                        newlplot.extend([lplot[i]] * (mlen + 1 - prevmlen))
                        prevmlen = mlen + 1

                    lplot = newlplot

            pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))
            plottedline = pltmethod(self.pinf.x, lplot, **plotkwargs)
            try:
                plottedline = plottedline[0]
            except:
                # Possibly a container of artists (when plotting bars)
                pass

            self.pinf.zorder[ax] = plottedline.get_zorder()

            if not math.isnan(lplot[-1]):
                # line has valid values, plot a tag for the last value
                self.drawtag(ax, len(self.pinf.xreal), lplot[-1],
                             facecolor='white',
                             edgecolor=self.pinf.color(ax))

        # plot subindicators that were created on self
        for subind in subinds:
            self.plotind(subind, subinds=self.dplotsover[subind], masterax=ax)

        if not masterax:
            # adjust margin if requested ... general of particular
            ymargin = ind.plotinfo._get('plotymargin', 0.0)
            ymargin = max(ymargin, self.pinf.sch.yadjust)
            if ymargin:
                ax.margins(y=ymargin)

            # Set specific or generic ticks
            yticks = ind.plotinfo._get('plotyticks', [])
            if not yticks:
                yticks = ind.plotinfo._get('plotyhlines', [])

            if yticks:
                ax.set_yticks(yticks)
            else:
                locator = mticker.MaxNLocator(nbins=4, prune='both')
                ax.yaxis.set_major_locator(locator)

            # Set specific hlines if asked to
            hlines = ind.plotinfo._get('plothlines', [])
            if not hlines:
                hlines = ind.plotinfo._get('plotyhlines', [])
            for hline in hlines:
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

        # plot subindicators on self with independent axis below
        for downind in downinds:
            self.plotind(downind)

    def plotvolume(self, data, opens, highs, lows, closes, volumes, label):
        if self.pinf.sch.voloverlay:
            rowspan = self.pinf.sch.rowsmajor
        else:
            rowspan = self.pinf.sch.rowsminor

        ax = self.newaxis(data.volume, rowspan=rowspan)

        if self.pinf.sch.voloverlay:
            volalpha = self.pinf.sch.voltrans
        else:
            volalpha = 1.0

        maxvol = volylim = max(volumes)
        if maxvol:
            # Plot the volume (no matter if as overlay or standalone)
            vollabel = label
            volplot, = plot_volume(ax, self.pinf.x, opens, closes, volumes,
                                   colorup=self.pinf.sch.volup,
                                   colordown=self.pinf.sch.voldown,
                                   alpha=volalpha, label=vollabel)

            nbins = 6
            prune = 'both'
            if self.pinf.sch.voloverlay:
                # store for a potential plot over it
                nbins = int(nbins / self.pinf.sch.volscaling)
                prune = None

                volylim /= self.pinf.sch.volscaling
                ax.set_ylim(0, volylim, auto=True)
            else:
                # plot a legend
                handles, labels = ax.get_legend_handles_labels()
                if handles:
                    # Legend done here to ensure it includes all plots
                    legend = ax.legend(loc=self.pinf.sch.legendindloc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

            locator = mticker.MaxNLocator(nbins=nbins, prune=prune)
            ax.yaxis.set_major_locator(locator)
            ax.yaxis.set_major_formatter(MyVolFormatter(maxvol))

        if not maxvol:
            ax.set_yticks([])
            return None

        return volplot

    def setxdata(self, data):
        # only if this data has a master, do something
        if data.mlen:
            # this data has a master, get the real length of this data
            self.pinf.xlen = len(data.mlen)
            # find the starting point with regards to master start: pstart
            self.pinf.xstart = bisect.bisect_left(
                data.mlen, self.pinf.pstart)

            # find the ending point with regards to master start: pend
            self.pinf.xend = bisect.bisect_right(
                data.mlen, self.pinf.pend)

            # extract the Xs from the subdata
            self.pinf.x = data.mlen[self.pinf.xstart:self.pinf.xend]
            # rebase the Xs to the start of the main data point
            self.pinf.x = [x - self.pinf.pstart for x in self.pinf.x]

    def plotdata(self, data, indicators):
        for ind in indicators:
            upinds = self.dplotsup[ind]
            for upind in upinds:
                self.plotind(upind,
                             subinds=self.dplotsover[upind],
                             upinds=self.dplotsup[upind],
                             downinds=self.dplotsdown[upind])

        # set the x axis data (if needed)
        self.setxdata(data)

        opens = data.open.plotrange(self.pinf.xstart, self.pinf.xend)
        highs = data.high.plotrange(self.pinf.xstart, self.pinf.xend)
        lows = data.low.plotrange(self.pinf.xstart, self.pinf.xend)
        closes = data.close.plotrange(self.pinf.xstart, self.pinf.xend)
        volumes = data.volume.plotrange(self.pinf.xstart, self.pinf.xend)

        vollabel = 'Volume'
        if self.pinf.sch.volume and self.pinf.sch.voloverlay:
            volplot = self.plotvolume(
                data, opens, highs, lows, closes, volumes, vollabel)
            axvol = self.pinf.daxis[data.volume]
            ax = axvol.twinx()
            self.pinf.daxis[data] = ax
        else:
            ax = self.newaxis(data, rowspan=self.pinf.sch.rowsmajor)

        datalabel = ''
        dataname = ''
        if hasattr(data, '_name') and data._name:
            datalabel += data._name

        if hasattr(data, '_compression') and \
           hasattr(data, '_timeframe'):
            tfname = TimeFrame.getname(data._timeframe, data._compression)
            datalabel += ' (%d %s)' % (data._compression, tfname)

        datalabel += ' O:%.2f H:%2.f L:%.2f C:%.2f' % \
                     (opens[-1], highs[-1], lows[-1], closes[-1])

        if self.pinf.sch.style.startswith('line'):
            plotted = plot_lineonclose(
                ax, self.pinf.x, closes,
                color=self.pinf.sch.loc, label=datalabel)
        else:
            if self.pinf.sch.style.startswith('candle'):
                plotted = plot_candlestick(
                    ax, self.pinf.x, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel)

            elif self.pinf.sch.style.startswith('bar') or True:
                # final default option -- should be "else"
                plotted = plot_ohlc(
                    ax, self.pinf.x, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel)

        self.pinf.zorder[ax] = plotted[0].get_zorder()

        # Code to place a label at the right hand side with the last value
        self.drawtag(ax, len(self.pinf.xreal), closes[-1],
                     facecolor='white', edgecolor=self.pinf.sch.loc)

        ax.yaxis.set_major_locator(mticker.MaxNLocator(prune='both'))
        # make sure "over" indicators do not change our scale
        ax.set_ylim(ax.get_ylim())

        if self.pinf.sch.volume:
            if not self.pinf.sch.voloverlay:
                self.plotvolume(
                    data, opens, highs, lows, closes, volumes, vollabel)
            else:
                # Prepare overlay scaling/pushup or manage own axis
                if self.pinf.sch.volpushup:
                    # push up overlaid axis by lowering the bottom limit
                    axbot, axtop = ax.get_ylim()
                    axbot *= (1.0 - self.pinf.sch.volpushup)
                    ax.set_ylim(axbot, axtop)

        for ind in indicators:
            self.plotind(ind, subinds=self.dplotsover[ind], masterax=ax)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            # put data and volume legend entries in the 1st positions
            # because they are "collections" they are considered after Line2D
            # for the legend entries, which is not our desire
            if self.pinf.sch.volume and self.pinf.sch.voloverlay:
                if volplot:
                    # even if volume plot was requested, there may be no volume
                    labels.insert(0, vollabel)
                    handles.insert(0, volplot)

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

        for ind in indicators:
            downinds = self.dplotsdown[ind]
            for downind in downinds:
                self.plotind(downind,
                             subinds=self.dplotsover[downind],
                             upinds=self.dplotsup[downind],
                             downinds=self.dplotsdown[downind])

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

            x._plotinit()  # will be plotted ... call its init function

            # support LineSeriesStub which has "owner" to point to the data
            key = getattr(x._clock, 'owner', x._clock)
            if key is strategy:  # a LinesCoupler
                key = strategy.data

            if getattr(x.plotinfo, 'plotforce', False):
                if key not in strategy.datas:
                    datas = strategy.datas
                    while True:
                        if key not in strategy.datas:
                            key = key._clock
                        else:
                            break

            if x.plotinfo.plotmaster is not None:
                key = x.plotinfo.plotmaster

            if x.plotinfo.subplot and not x.plotinfo.plotmaster:
                if x.plotinfo.plotabove:
                    self.dplotsup[key].append(x)
                else:
                    self.dplotsdown[key].append(x)
            else:
                self.dplotsover[key].append(x)
