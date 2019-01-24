import collections
from array import array

import backtrader as bt

from .utils import get_strategy_label, get_data_obj
from .utils import convert_to_pandas, nanfilt
from .utils import resample_line
from .utils import convert_color, sanitize_source_name, get_bar_width, convert_linestyle, adapt_yranges

from bokeh.models import Span
from bokeh.plotting import figure
from bokeh.models import HoverTool, CrosshairTool
from bokeh.models import LinearAxis, DataRange1d, Renderer
from bokeh.models.formatters import NumeralTickFormatter
from bokeh.models import ColumnDataSource, FuncTickFormatter, DatetimeTickFormatter


class HoverContainer(object):
    """Class to store information about hover tooltips. Will be filled while Bokeh glyphs are created. After all figures are complete, hovers will be applied"""
    def __init__(self):
        self._hover_tooltips = collections.defaultdict(list)
        self._hover_tooltips_data = collections.defaultdict(list)

    def add_hovertip(self, label, tmpl, target_figure=None):
        """hover_target being None means all"""
        self._hover_tooltips[target_figure].append((label, tmpl))

    def add_hovertip_for_data(self, label, tmpl, target_data):
        """adds a hovertip for a target data"""
        self._hover_tooltips_data[target_data].append((label, tmpl))

    def apply_hovertips(self, figures):
        """Add hovers to to all figures from the figures list"""
        for f in figures:
            for t in f.figure.tools:
                if not isinstance(t, HoverTool):
                    continue

                hv = self._hover_tooltips[None]
                t.tooltips += hv

                if f.figure in self._hover_tooltips:
                    t.tooltips += self._hover_tooltips[f.figure]

                for d in f.datas:
                    if d in self._hover_tooltips_data:
                        t.tooltips += self._hover_tooltips_data[d]


class Figure(object):
    _tools = "pan,box_zoom,xwheel_zoom,reset"

    def __init__(self, strategy, cds, hoverc, start, end, scheme, master_type, plotabove):
        self._strategy = strategy
        self._cds: ColumnDataSource = cds
        self._hoverc = hoverc
        self._scheme = scheme
        self._start = start
        self._end = end
        self.figure = None
        self._hover = None
        self._coloridx = collections.defaultdict(lambda: -1)
        self._hover_line_set = False
        self.master_type = master_type
        self.plotabove = plotabove
        self.datas = []  # list of all datas that have been plotted to this figure
        self._init_figure()

    def _set_single_hover_renderer(self, ren):
        """Sets this figure's hover to a single renderer"""
        if self._hover_line_set:
            return

        self._hover.renderers = [ren]
        self._hover_line_set = True

    def _add_hover_renderer(self, ren):
        """Adds another hover render target. Only has effect if not single renderer has been set before"""
        if self._hover_line_set:
            return

        if isinstance(self._hover.renderers, list):
            self._hover.renderers.append(ren)
        else:
            self._hover.renderers = [ren]


    def _nextcolor(self, key=None):
        self._coloridx[key] += 1
        return self._coloridx[key]

    def _color(self, key: object=None):
        return convert_color(self._scheme.color(self._coloridx[key]))

    def _init_figure(self):
        # plot height will be set later
        f = figure(tools=Figure._tools, plot_width=self._scheme.plot_width, sizing_mode='scale_width', x_axis_type='linear')

        # TODO: backend webgl (output_backend="webgl") removed due to this bug:
        # https://github.com/bokeh/bokeh/issues/7568

        f.border_fill_color = convert_color(self._scheme.border_fill)

        f.xaxis.axis_line_color = convert_color(self._scheme.axis_line_color)
        f.yaxis.axis_line_color = convert_color(self._scheme.axis_line_color)
        f.xaxis.minor_tick_line_color = convert_color(self._scheme.tick_line_color)
        f.yaxis.minor_tick_line_color = convert_color(self._scheme.tick_line_color)
        f.xaxis.major_tick_line_color = convert_color(self._scheme.tick_line_color)
        f.yaxis.major_tick_line_color = convert_color(self._scheme.tick_line_color)

        f.xaxis.major_label_text_color = convert_color(self._scheme.axis_label_text_color)
        f.yaxis.major_label_text_color = convert_color(self._scheme.axis_label_text_color)

        f.xgrid.grid_line_color = convert_color(self._scheme.grid_line_color)
        f.ygrid.grid_line_color = convert_color(self._scheme.grid_line_color)
        f.title.text_color = convert_color(self._scheme.plot_title_text_color)

        f.left[0].formatter.use_scientific = False
        f.background_fill_color = convert_color(self._scheme.background_fill)

        # mechanism for proper date axis without gaps, thanks!
        # https://groups.google.com/a/continuum.io/forum/#!topic/bokeh/t3HkalO4TGA
        f.xaxis.formatter = FuncTickFormatter(
            args=dict(
                axis=f.xaxis[0],
                formatter=DatetimeTickFormatter(days=['%d %b', '%a %d'],
                                                months=['%m/%Y', "%b %y"]),
                source=self._cds,
            ),
            code="""
                axis.formatter.doFormat = function (ticks) {
                    const dates = ticks.map(i => source.data.datetime[i]),
                          valid = t => t !== undefined,
                          labels = formatter.doFormat(dates.filter(valid));
                    let i = 0;
                    return dates.map(t => valid(t) ? labels[i++] : '');
                };
                const axisticks = axis.tick_coords.major[0],
                      labels = axis.formatter.doFormat(ticks);
                return labels[axisticks.indexOf(tick)];
        """)

        ch = CrosshairTool(line_color=self._scheme.crosshair_line_color)
        f.tools.append(ch)

        h = HoverTool(tooltips=[('Time', '@datetime{%x %X}')],
                      mode="vline",
                      formatters={'datetime': 'datetime'}
                      )
        f.tools.append(h)

        self._hover = h
        self.figure = f

    def plot(self, obj, strat_clk, master=None):
        if isinstance(obj, bt.feeds.DataBase):
            self.plot_data(obj, master, strat_clk)
            height_set = self._scheme.plot_height_data
        elif isinstance(obj, bt.indicator.Indicator):
            self.plot_indicator(obj, master, strat_clk)
            height_set = self._scheme.plot_height_indicator
        elif isinstance(obj, bt.observers.Observer):
            self.plot_observer(obj, master)
            height_set = self._scheme.plot_height_observer
        else:
            raise Exception("Unsupported plot object: {}".format(type(obj)))

        self.datas.append(obj)

        # set height according to master type
        if master is None:
            self.figure.plot_height = height_set

    @staticmethod
    def _get_datas_description(ind):
        """Returns a string listing all involved data feeds. Empty string if there is only a single feed in the mix"""
        names = []
        for x in ind.datas:
            if isinstance(x, bt.DataBase):
                # for pandas feed _dataname is a DataFrame
                # names.append(x._dataname)
                names.append(x._name)
            elif isinstance(x, bt.Indicator):
                names.append(x.plotlabel())
        return "({})".format(','.join(names))

    def plot_observer(self, obj, master):
        self.plot_indicator(obj, master)

    def plot_indicator(self, obj, master, strat_clk=None):
        pl =  '{} '.format(obj.plotlabel())
        if isinstance(obj, bt.Indicator):
            pl += Figure._get_datas_description(obj)
        elif isinstance(obj, bt.Observer):
            pl += get_strategy_label(type(obj._owner), obj._owner.params, self._scheme.number_format)

        self._figure_append_title(pl)
        indlabel = obj.plotlabel()
        plotinfo = obj.plotinfo

        for lineidx in range(obj.size()):
            line = obj.lines[lineidx]
            source_id = Figure._source_id(line)
            linealias = obj.lines._getlinealias(lineidx)

            lineplotinfo = getattr(obj.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(obj.plotlines, linealias, None)

            if not lineplotinfo:
                lineplotinfo = bt.AutoInfoClass()

            if lineplotinfo._get('_plotskip', False):
                continue

            marker = lineplotinfo._get("marker", None)
            method = lineplotinfo._get('_method', "line")

            color = getattr(lineplotinfo, "color", None)
            if color is None:
                if not lineplotinfo._get('_samecolor', False):
                    self._nextcolor()
                color = self._color()
            color = convert_color(color)

            kwglyphs = {'name': linealias}

            dataline = line.plotrange(self._start, self._end)
            line_clk = get_data_obj(obj._clock).lines.datetime.plotrange(self._start, self._end)
            dataline = resample_line(dataline, line_clk, strat_clk)
            self._add_to_cds(dataline, source_id)

            label = None
            if master is None or lineidx == 0 or plotinfo.plotlinelabels:
                label = indlabel
                if master is None or plotinfo.plotlinelabels:
                    label += " " + (lineplotinfo._get("_name", "") or linealias)
            kwglyphs['legend'] = label

            if marker is not None:
                kwglyphs['size'] = lineplotinfo.markersize * 1.2
                kwglyphs['color'] = color
                kwglyphs['y'] = source_id

                mrk_fncs = {'^': self.figure.triangle,
                            'v': self.figure.inverted_triangle,
                            'o': self.figure.circle,

                            '<': self.figure.circle_cross,
                            '>': self.figure.circle_x,
                            '1': self.figure.diamond,
                            '2': self.figure.diamond_cross,
                            '3': self.figure.hex,
                            '4': self.figure.square,
                            '8': self.figure.square_cross,
                            's': self.figure.square_x,
                            'p': self.figure.triangle,
                            '*': self.figure.asterisk,
                            'h': self.figure.hex,
                            'H': self.figure.hex,
                            '+': self.figure.asterisk,
                            'x': self.figure.x,
                            'D': self.figure.diamond_cross,
                            'd': self.figure.diamond,
                            }
                if marker not in mrk_fncs:
                    raise Exception("Sorry, unsupported marker: '{}'. Please report to GitHub.".format(marker))
                glyph_fnc = mrk_fncs[marker]
            elif method == "bar":
                kwglyphs['bottom'] = 0
                kwglyphs['line_color'] = None
                kwglyphs['fill_color'] = color
                kwglyphs['width'] = get_bar_width()
                kwglyphs['top'] = source_id

                glyph_fnc = self.figure.vbar
            elif method == "line":
                kwglyphs['line_width'] = 1
                kwglyphs['color'] = color
                kwglyphs['y'] = source_id

                linestyle = getattr(lineplotinfo, "ls", None)
                if linestyle is not None:
                    kwglyphs['line_dash'] = convert_linestyle(linestyle)

                glyph_fnc = self.figure.line
            else:
                raise Exception("Unknown plotting method '{}'".format(method))

            renderer = glyph_fnc("index", source=self._cds, **kwglyphs)

            # for markers add additional renderer so hover pops up for all of them
            if marker is None:
                self._set_single_hover_renderer(renderer)
            else:
                self._add_hover_renderer(renderer)

            hover_label = "{} - {}".format(indlabel, linealias)
            hover_data = "@{}{{{}}}".format(source_id, self._scheme.number_format)
            if not self._scheme.merge_data_hovers:
                # add hover tooltip for indicators/observers's data
                self._hoverc.add_hovertip_for_data(hover_label, hover_data, obj._clock)
            else:
                hover_target = None
                is_obs = isinstance(obj, bt.Observer)
                if is_obs and master is None:
                    hover_target = self.figure
                # add hover tooltip for all figures
                self._hoverc.add_hovertip(hover_label, hover_data, hover_target)

            # adapt y-axis if needed
            if master is None or getattr(master.plotinfo, 'plotylimited', False) is False:
                adapt_yranges(self.figure.y_range, dataline)

        self._set_yticks(obj)
        self._plot_hlines(obj)

    def _set_yticks(self, obj):
        yticks = obj.plotinfo._get('plotyticks', [])
        if not yticks:
            yticks = obj.plotinfo._get('plotyhlines', [])

        if yticks:
            self.figure.yaxis.ticker = yticks

    def _plot_hlines(self, obj):
        hlines = obj.plotinfo._get('plothlines', [])
        if not hlines:
            hlines = obj.plotinfo._get('plotyhlines', [])

        # Horizontal Lines
        hline_color = convert_color(self._scheme.hlinescolor)
        for hline in hlines:
            span = Span(location=hline,
                        dimension='width',
                        line_color=hline_color,
                        line_dash=convert_linestyle(self._scheme.hlinesstyle),
                        line_width=self._scheme.hlineswidth)
            self.figure.renderers.append(span)

    def _figure_append_title(self, title):
        # append to title
        if len(self.figure.title.text) > 0:
            self.figure.title.text += " / "
        self.figure.title.text += title

    def _add_to_cds(self, data, name):
        if name in self._cds.column_names:
            return
        self._cds.add(data, name)

    @staticmethod
    def _source_id(source):
        return str(id(source))

    def plot_data(self, data, master, strat_clk=None):
        source_id = Figure._source_id(data)
        title = sanitize_source_name(data._name or '<NoName>')
        if len(data._env.strats) > 1:
            title += ' ({})'.format(get_strategy_label(type(self._strategy), self._strategy.params, self._scheme.number_format))

        # append to title
        self._figure_append_title(title)

        df = convert_to_pandas(strat_clk, data, self._start, self._end)

        # configure colors
        colorup = convert_color(self._scheme.barup)
        colordown = convert_color(self._scheme.bardown)
        colorup_wick = convert_color(self._scheme.barup_wick)
        colordown_wick = convert_color(self._scheme.bardown_wick)
        colorup_outline = convert_color(self._scheme.barup_outline)
        colordown_outline = convert_color(self._scheme.bardown_outline)
        is_up = df.close > df.open

        self._add_to_cds(df.open, source_id + 'open')
        self._add_to_cds(df.high, source_id + 'high')
        self._add_to_cds(df.low, source_id + 'low')
        self._add_to_cds(df.close, source_id + 'close')
        self._add_to_cds([colorup if x else colordown for x in is_up], source_id + 'colors_bars')
        self._add_to_cds([colorup_wick if x else colordown_wick for x in is_up], source_id + 'colors_wicks')
        self._add_to_cds([colorup_outline if x else colordown_outline for x in is_up], source_id + 'colors_outline')

        if self._scheme.style == 'line':
            if data.plotinfo.plotmaster is None:
                color = convert_color(self._scheme.loc)
            else:
                self._nextcolor(data.plotinfo.plotmaster)
                color = convert_color(self._color(data.plotinfo.plotmaster))

            renderer = self.figure.line('index', source_id + 'close', source=self._cds, line_color=color, legend=data._name)
            self._set_single_hover_renderer(renderer)

            self._hoverc.add_hovertip("Close", "@{}close{{({})}}".format(source_id, self._scheme.number_format))
            # self._hoverc.add_hovertip("Close", '@{}close'.format(source_id))
        elif self._scheme.style == 'bar':
            self.figure.segment('index', source_id + 'high', 'index', source_id + 'low', source=self._cds, color=source_id + 'colors_wicks', legend=data._name)
            renderer = self.figure.vbar('index',
                                        get_bar_width(),
                                        source_id + 'open',
                                        source_id + 'close',
                                        source=self._cds,
                                        fill_color=source_id + 'colors_bars',
                                        line_color=source_id + 'colors_outline')

            self._set_single_hover_renderer(renderer)

            hover_target = None if self._scheme.merge_data_hovers else self.figure
            self._hoverc.add_hovertip("Open", "@{}open{{({})}}".format(source_id, self._scheme.number_format), hover_target)
            self._hoverc.add_hovertip("High", "@{}high{{({})}}".format(source_id, self._scheme.number_format), hover_target)
            self._hoverc.add_hovertip("Low", "@{}low{{({})}}".format(source_id, self._scheme.number_format), hover_target)
            self._hoverc.add_hovertip("Close", "@{}close{{({})}}".format(source_id, self._scheme.number_format), hover_target)

        else:
            raise Exception("Unsupported style '{}'".format(self._scheme.style))

        adapt_yranges(self.figure.y_range, df.low, df.high)

        # check if we have to plot volume overlay
        if self._scheme.volume and self._scheme.voloverlay:
            self.plot_volume(data, strat_clk, self._scheme.voltrans, True)

    def plot_volume(self, data, strat_clk, alpha, extra_axis=False):
        source_id = Figure._source_id(data)

        df = convert_to_pandas(strat_clk, data, self._start, self._end)

        if len(nanfilt(df.volume)) == 0:
            return

        colorup = convert_color(self._scheme.volup)
        colordown = convert_color(self._scheme.voldown)

        is_up = df.close > df.open
        colors = [colorup if x else colordown for x in is_up]

        self._add_to_cds(df.volume, '{}volume'.format(source_id))
        self._add_to_cds(colors, '{}volume_colors'.format(source_id))

        kwargs = {'fill_alpha': alpha,
                  'line_alpha': alpha,
                  'name': 'Volume',
                  'legend': 'Volume'}

        ax_formatter = NumeralTickFormatter(format=self._scheme.number_format)

        if extra_axis:
            self.figure.extra_y_ranges = {'axvol': DataRange1d()}
            adapt_yranges(self.figure.extra_y_ranges['axvol'], df.volume)
            self.figure.extra_y_ranges['axvol'].end /= self._scheme.volscaling

            ax_color = colorup

            ax = LinearAxis(y_range_name="axvol", formatter=ax_formatter,
                            axis_label_text_color=ax_color, axis_line_color=ax_color, major_label_text_color=ax_color,
                            major_tick_line_color=ax_color, minor_tick_line_color=ax_color)
            self.figure.add_layout(ax, 'left')
            kwargs['y_range_name'] = "axvol"
        else:
            self.figure.yaxis.formatter = ax_formatter

            adapt_yranges(self.figure.y_range, df.volume)
            self.figure.y_range.end /= self._scheme.volscaling

        self.figure.vbar('index', get_bar_width(), '{}volume'.format(source_id), 0, source=self._cds, fill_color='{}volume_colors'.format(source_id), line_color=None, **kwargs)

        hover_target = None if self._scheme.merge_data_hovers else self.figure
        self._hoverc.add_hovertip("Volume", "@{}volume{{({})}}".format(source_id, self._scheme.number_format), hover_target)

