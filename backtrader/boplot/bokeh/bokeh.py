from .utils import generate_stylesheet
import bisect
import os
import sys
import tempfile
import datetime
import backtrader as bt

try:
    from bokeh.models import ColumnDataSource, Model, Paragraph
    from bokeh.models.widgets import Panel, Tabs, DataTable, TableColumn
    from bokeh.layouts import column, gridplot, row
    from bokeh.server.server import Server
    from bokeh.document import Document
    from bokeh.application import Application
    from bokeh.application.handlers.function import FunctionHandler
    from bokeh.embed import file_html
    from bokeh.models.widgets import NumberFormatter, StringFormatter
    from bokeh.resources import CDN
    from bokeh.util.browser import view
except ImportError as e:
    raise ImportError(
        'Bokeh seems to be missing. Needed for bokeh plotting support')

from ..utils import get_strategy_label, get_data_obj
from ... import bttypes

from .figure import Figure, HoverContainer
from .datatable import TableGenerator
from ..schemes import Tradimo
from ..schemes.scheme import Scheme
import logging
from array import array

try:
    from jinja2 import Environment, PackageLoader
except ImportError as e:
    raise ImportError(
        'jinja2 seems to be missing. Needed for bokeh plotting support')

_logger = logging.getLogger(__name__)

if 'ipykernel' in sys.modules:
    from IPython.core.display import display, HTML
    from bokeh.io import output_notebook, show
    output_notebook()


class FigurePage(object):
    def __init__(self):
        self.figures = []
        self.cds = None
        self.analyzers = []
        self.strategies = None
        self.current_strategy_cls = None
        self.current_strategy_params = None


class Bokeh(metaclass=bt.MetaParams):
    params = (('scheme', Tradimo()),
              ('filename', None))

    def __init__(self, **kwargs):
        for pname, pvalue in kwargs.items():
            setattr(self.p.scheme, pname, pvalue)

        self._iplot: bool = None
        self._data_graph = None
        self._volume_graphs = None
        self._num_plots = 0
        self._tablegen = TableGenerator(self.p.scheme)
        if not isinstance(self.p.scheme, Scheme):
            raise Exception("Provided scheme has to be a subclass of backtrader.boplot.schemes.scheme.Scheme")

        self._fp = FigurePage()

    def _build_graph(self, datas, inds, obs):
        self._data_graph = {}
        self._volume_graphs = []
        for d in datas:
            if not d.plotinfo.plot:
                continue

            pmaster = Bokeh._resolve_plotmaster(d.plotinfo.plotmaster)
            if pmaster is None:
                self._data_graph[d] = []
            else:
                if pmaster not in self._data_graph:
                    self._data_graph[pmaster] = []
                self._data_graph[pmaster].append(d)

            if self.p.scheme.volume and self.p.scheme.voloverlay is False:
                self._volume_graphs.append(d)

        # Sort observers in the different lists/dictionaries
        for o in obs:
            if not o.plotinfo.plot or o.plotinfo.plotskip:
                continue

            if o.plotinfo.subplot:
                self._data_graph[o] = []
            else:
                pmaster = Bokeh._resolve_plotmaster(o.plotinfo.plotmaster or o.data)
                if pmaster not in self._data_graph:
                    self._data_graph[pmaster] = []
                self._data_graph[pmaster].append(o)

        for ind in inds:
            if not hasattr(ind, 'plotinfo'):
                # no plotting support - so far LineSingle derived classes
                continue

            # should this indicator be plotted?
            if not ind.plotinfo.plot or ind.plotinfo.plotskip:
                continue

            # subplot = create a new figure for this indicator
            subplot = ind.plotinfo.subplot
            if subplot:
                self._data_graph[ind] = []
            else:
                pm = ind.plotinfo.plotmaster if ind.plotinfo.plotmaster is not None else ind.data
                pm = get_data_obj(pm)
                pmaster = Bokeh._resolve_plotmaster(pm)
                if pmaster not in self._data_graph:
                    self._data_graph[pmaster] = []
                self._data_graph[pmaster].append(ind)

    @property
    def figures(self):
        return self._fp.figures

    @staticmethod
    def _resolve_plotmaster(obj):
        if obj is None:
            return None

        while True:
            pm = obj.plotinfo.plotmaster
            if pm is None:
                break
            else:
                obj = pm
        return obj

    @staticmethod
    def _get_start_end(strategy, start, end):
        st_dtime = strategy.lines.datetime.array
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, bt.date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, bt.date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  # -1 =  len() -2 = len() - 1

        return start, end

    def generate_result_model(self, result, columns=None, num_item_limit=None):
        """Generates a model from a result object"""
        if bttypes.is_optresult(result) or bttypes.is_ordered_optresult(result):
            return self.generate_optresult_model(result, columns, num_item_limit)
        elif bttypes.is_btresult(result):
            for s in result:
                self.plot(s)
            return self.generate_model()
        else:
            raise Exception('Unsupported result type: {}'.format(str(result)))

    def visualize(self, result, columns=None, iplot=False, start=None, end=None):
        """Visualize a cerebro result. Pass either a list of strategies or a list of list of optreturns"""
        filenames = []
        if bttypes.is_optresult(result) or bttypes.is_ordered_optresult(result):
            # this will not complete the call, starts a blocking server
            self.run_optresult_server(result, columns)
        elif bttypes.is_btresult(result):
            for s in result:
                self.plot(s, iplot, start, end)
            filenames.append(self.show())
        else:
            raise Exception('Unsupported result type: {}'.format(str(result)))

        return filenames

    def plot(self, obj, iplot=False, start=None, end=None):
        """Called by backtrader to plot either a strategy or an optimization results"""

        self._iplot = iplot and 'ipykernel' in sys.modules

        if isinstance(obj, bt.Strategy):
            self._fp.current_strategy_cls = obj.__class__
            self._fp.current_strategy_params = obj.params
            self._blueprint_strategy(obj, start, end)
        elif isinstance(obj, bttypes.OptReturn):
            self._fp.current_strategy_cls = obj.strategycls
            self._fp.current_strategy_params = obj.params

            self._fp.analyzers = [a for _, a in obj.analyzers.getitems()]
        else:
            raise Exception('Unsupported plot source object: {}'.format(str(type(obj))))
        return [self._fp]

    def show(self):
        """Called by backtrader to display a figure"""
        model = self.generate_model()
        filename = None
        if self._iplot:
            css = self._output_stylesheet()
            display(HTML(css))
            show(model)
        else:
            filename = self._output_plot_file(model, self.p.filename)
            view(filename)

        self._reset()
        self._num_plots += 1

        return filename


    def savefig(self, fig, filename, width, height, dpi, tight):
        self._generate_output(fig, filename)
    #  endregion

    def _blueprint_strategy(self, strategy, start=None, end=None):
        if not strategy.datas:
            return

        if not len(strategy):
            return

        strat_figures = []
        self._fp.analyzers = [a for _, a in strategy.analyzers.getitems() if a.p.plot is True ]


        st_dtime = strategy.lines.datetime.plot()
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, bt.date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, bt.date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  # -1 =  len() -2 = len() - 1

        # TODO: using a pandas.DataFrame is desired. On bokeh 0.12.13 this failed cause of this issue:
        # https://github.com/bokeh/bokeh/issues/7400
        strat_clk: array[float] = strategy.lines.datetime.plotrange(start, end)

        if self._fp.cds is None:
            # we use timezone of first data
            dtline = [bt.num2date(x, strategy.datas[0]._tz) for x in strat_clk]

            # add an index line to use as x-axis (instead of datetime axis) to avoid datetime gaps (e.g. weekends)
            indices = list(range(0, len(dtline)))
            self._fp.cds = ColumnDataSource(data=dict(datetime=dtline, index=indices))

        self._build_graph(strategy.datas, strategy.getindicators(), strategy.getobservers())

        start, end = Bokeh._get_start_end(strategy, start, end)

        # reset hover container to not mix hovers with other strategies
        hoverc = HoverContainer()

        for master, slaves in self._data_graph.items():
            plotabove = getattr(master.plotinfo, 'plotabove', False)
            bf = Figure(strategy, self._fp.cds, hoverc, start, end, self.p.scheme, type(master), plotabove)
            strat_figures.append(bf)

            bf.plot(master, strat_clk, None)

            for s in slaves:
                bf.plot(s, strat_clk, master)

        for v in self._volume_graphs:
            bf = Figure(strategy, self._fp.cds, hoverc, start, end, self.p.scheme)
            bf.plot_volume(v, strat_clk, 1.0, start, end)

        # apply legend click policy
        for f in strat_figures:
            f.figure.legend.click_policy = self.p.scheme.legend_click

        for f in strat_figures:
            f.figure.legend.background_fill_color = self.p.scheme.legend_background_color
            f.figure.legend.label_text_color = self.p.scheme.legend_text_color

        # link axis
        for i in range(1, len(strat_figures)):
            strat_figures[i].figure.x_range = strat_figures[0].figure.x_range

        # configure xaxis visibility
        if self.p.scheme.xaxis_pos == "bottom":
            for i, f in enumerate(strat_figures):
                f.figure.xaxis.visible = False if i <= len(strat_figures) else True

        hoverc.apply_hovertips(strat_figures)

        self._fp.figures += strat_figures

    def plot_and_generate_model(self, strats):
        self._reset()
        for strat in strats:
            self.plot(strat)
        return self.generate_model()

    # region Generator Methods
    def generate_model(self):
        """Returns a model generated from internal blueprints"""
        if self.p.scheme.plot_mode == 'single':
            return self._generate_model_single(self._fp)
        elif self.p.scheme.plot_mode == 'tabs':
            return self._generate_model_tabs(self._fp)
        else:
            raise Exception('Unsupported plot mode: {}'.format(self.p.scheme.plot_mode))

    def _generate_model_single(self, fp):
        """Print all figures in one column. Plot observers first, then all plotabove then rest"""
        figs = list(fp.figures)
        observers = [x for x in figs if issubclass(x.master_type, bt.Observer)]
        figs = [x for x in figs if x not in observers]
        aboves = [x for x in figs if x.plotabove]
        figs = [x for x in figs if x not in aboves]
        figs = [x.figure for x in observers + aboves + figs]

        panels = []
        if len(figs) > 0:
            chart_grid = gridplot([[x] for x in figs], sizing_mode='fixed', toolbar_location='left', toolbar_options={'logo': None})
            panels.append(Panel(child=chart_grid, title="Charts"))

        panel_analyzers = self._get_analyzer_tab(fp)
        if panel_analyzers is not None:
            panels.append(panel_analyzers)

        return Tabs(tabs=panels)

    def _generate_model_tabs(self, fp):
        figs = list(fp.figures)
        observers = [x for x in figs if issubclass(x.master_type, bt.Observer)]
        datas = [x for x in figs if issubclass(x.master_type, bt.DataBase)]
        inds = [x for x in figs if issubclass(x.master_type, bt.Indicator)]

        panels = []

        def add_panel(obj, title):
            if len(obj) == 0:
                return
            g = gridplot([[x.figure] for x in obj], sizing_mode='fixed', toolbar_location='left', toolbar_options={'logo': None})
            panels.append(Panel(title=title, child=g))

        add_panel(datas, "Datas")
        add_panel(inds, "Indicators")
        add_panel(observers, "Observers")

        p_analyzers = self._get_analyzer_tab(fp)
        if p_analyzers is not None:
            panels.append(p_analyzers)

        return Tabs(tabs=panels)
    # endregion

    def _get_analyzer_tab(self, fp):
        def _get_column_row_count(col):
            return sum([x.height for x in col if x.height is not None])

        if len(fp.analyzers) == 0:
            return None

        table_width = int(self.p.scheme.analyzer_tab_width / self.p.scheme.analyzer_tab_num_cols)
        col_childs = []
        for _ in range(0, self.p.scheme.analyzer_tab_num_cols):
            col_childs.append([])

        plottable_analyzers = (a for a in fp.analyzers if a.p.plot is True)
        for a in plottable_analyzers:
            table_header, elements = self._tablegen.get_analyzers_tables(a, table_width)

            col_childs = sorted(col_childs, key=lambda x: _get_column_row_count(x))
            col_childs[0] += [table_header] + elements

        childs = []
        for c in col_childs:
            if len(c) == 0:
                break
            childs.append(column(children=c, sizing_mode='fixed'))

        if fp.current_strategy_params is not None:
            s_params = get_strategy_label(fp.current_strategy_cls, fp.current_strategy_params, self.p.scheme.number_format)
            strat_params = Paragraph(text=s_params, width=self.p.scheme.plot_width, style={'font-size': 'large'})
            m = column([strat_params, row(children=childs, sizing_mode='fixed')])
        else:
            m = row(children=childs, sizing_mode='fixed')

        return Panel(child=m, title="Analyzers")

    def _output_stylesheet(self, template="basic.css.j2"):
        return generate_stylesheet(self.p.scheme, template)

    def _output_plot_file(self, model, filename=None, template="basic.html.j2"):
        if filename is None:
            tmpdir = tempfile.gettempdir()
            filename = os.path.join(tmpdir, 'bt_bokeh_plot_{}.html'.format(self._num_plots))

        env = Environment(loader=PackageLoader('backtrader.boplot.bokeh', 'templates'))
        title = 'BackTest {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        templ = env.get_template(template)
        templ.globals['title'] = title

        html = file_html(model,
                         template=templ,
                         title=title,
                         resources=CDN,
                         template_variables=dict(
                             stylesheet=self._output_stylesheet(),
                             show_headline=self.p.scheme.show_headline,
                             )
                         )

        with open(filename, 'w') as f:
            f.write(html)

        return filename

    def _reset(self):
        self._fp = FigurePage()

    @staticmethod
    def _get_limited_optresult(optresult, num_item_limit=None):
        if num_item_limit is None:
            return optresult
        return optresult[0:num_item_limit]

    @staticmethod
    def _get_opt_count(optresult):
        if isinstance(optresult[0], dict):
            # OrderedOptResult
            return len(optresult['optresult'][0]['result'])
        else:
            # OptResult
            return len(optresult[0])

    def generate_optresult_model(self, optresult, columns=None, num_item_limit=None):
        """Generates and returns an interactive model for an OptResult or an OrderedOptResult"""
        cds = ColumnDataSource()
        tab_columns = []

        col_formatter_num = NumberFormatter(format=self.p.scheme.number_format)
        col_formatter_str = StringFormatter()
        opts = optresult if bttypes.is_optresult(optresult) else [x.result for x in optresult.optresult]
        if bttypes.is_ordered_optresult(optresult):
            benchmarks = [x.benchmark for x in Bokeh._get_limited_optresult(optresult.optresult, num_item_limit)]
            cds.add(benchmarks, "benchmark")
            tab_columns.append(TableColumn(field='benchmark', title=optresult.benchmark_label, sortable=False, formatter=col_formatter_num))

        for idx, strat in enumerate(opts[0]):
            # add suffix when dealing with more than 1 strategy
            strat_suffix = ''
            if len(opts[0]) > 1:
                strat_suffix = ' [{}]'.format(idx)

            for name, val in strat.params._getitems():
                tab_columns.append(TableColumn(field='{}_{}'.format(idx, name), title='{}{}'.format(name, strat_suffix), sortable=False))

                # get value for the current param for all results
                pvals = []
                for opt in Bokeh._get_limited_optresult(opts, num_item_limit):
                    pvals.append(opt[idx].params._get(name))
                cds.add(pvals, '{}_{}'.format(idx, name))

        # add user columns specified by parameter 'columns'
        if columns is not None:
            for k, v in columns.items():
                ll = [str(v(x)) for x in Bokeh._get_limited_optresult(optresult, num_item_limit)]
                cds.add(ll, k)
                tab_columns.append(TableColumn(field=k, title=k, sortable=False, formatter=col_formatter_str))

        selector = DataTable(source=cds, columns=tab_columns, width=self.p.scheme.plot_width, height=150)
        title = Paragraph(text="Optimization Results", width=self.p.scheme.plot_width, style={'font-size': 'large'})

        model = column([title, selector, self.plot_and_generate_model(opts[0])])

        def update(_name, _old, new):
            if len(new) == 0:
                return

            stratidx = new[0]
            model.children[-1] = self.plot_and_generate_model(opts[stratidx])

        cds.selected.on_change('indices', update)
        return model

    def run_optresult_server(self, result, columns=None):
        """Serves an optimization resulst as a Bokeh application running on a web server"""
        def make_document(doc: Document):
            doc.title = 'BackTest (Optimization) ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            env = Environment(loader=PackageLoader('backtrader.boplot.bokeh', 'templates'))
            templ = env.get_template("basic.html.j2")
            templ.globals['title'] = 'BackTest (Optimization) {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            templ.globals['show_headline'] = self.p.scheme.show_headline
            templ.globals['stylesheet'] = self._output_stylesheet()
            doc.template = templ

            model = self.generate_optresult_model(result, columns)
            doc.add_root(model)

        Bokeh._run_server(make_document)

    @staticmethod
    def _run_server(fnc_make_document, iplot=True, notebook_url="localhost:8889", port=8080):
        """Runs a Bokeh webserver application. Documents will be created using fnc_make_document"""
        handler = FunctionHandler(fnc_make_document)
        app = Application(handler)
        if iplot and 'ipykernel' in sys.modules:
            show(app, notebook_url=notebook_url)
        else:
            apps = {'/': app}

            print("Running optimization server.")
            server = Server(apps, port=port)
            server.io_loop.add_callback(server.show, "/")
            server.run_until_shutdown()
    #  endregion
