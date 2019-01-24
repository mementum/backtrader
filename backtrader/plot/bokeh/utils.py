from jinja2 import Environment, PackageLoader
from datetime import datetime
import matplotlib.colors
import backtrader as bt
import math
import numbers
import logging

try:
    import pandas
except ImportError:
    raise ImportError(
        'Pandas seems to be missing. Needed for bokeh plotting support')

_logger = logging.getLogger(__name__)


def convert_color(color):
    """if color is a float value then it is interpreted as a shade of grey and converted to the corresponding html color code"""
    try:
        val = round(float(color) * 255.0)
        hex_string = '#{0:02x}{0:02x}{0:02x}'.format(val)
        return hex_string
    except ValueError:
        return matplotlib.colors.to_hex(color)


def sanitize_source_name(name):
    """removes illegal characters from source name to make it compatible with Bokeh"""
    forbidden_chars = ' (),.-/*:'
    for fc in forbidden_chars:
        name = name.replace(fc, '_')
    return name


def get_bar_width():
    return 0.5


_style_mpl2bokeh = {
    '-': 'solid',
    '--': 'dashed',
    ':': 'dotted',
    '.-': 'dotdash',
    '-.': 'dashdot',
}


def convert_linestyle(style):
    """Converts a backtrader/matplotlib style string to bokeh style string"""
    return _style_mpl2bokeh[style]


def adapt_yranges(y_range, data_min, data_max=None):
    dmin = min(nanfilt(data_min), default=None)
    dmax = max(nanfilt(data_max if data_max is not None else data_min), default=None)

    if dmin is None or dmax is None:
        return

    diff = ((dmax - dmin) or dmin) * 0.1
    dmin -= diff
    dmax += diff

    if y_range.start is not None:
        dmin = min(dmin, y_range.start)
    y_range.start = dmin

    if y_range.end is not None:
        dmax = max(dmax, y_range.end)
    y_range.end = dmax


def generate_stylesheet(scheme, template="basic.css.j2"):
    env = Environment(loader=PackageLoader('backtrader.plot.bokeh', 'templates'))
    templ = env.get_template(template)

    css = templ.render(dict(
                             datatable_row_color_even=scheme.table_color_even,
                             datatable_row_color_odd=scheme.table_color_odd,
                             datatable_header_color=scheme.table_header_color,
                             tab_active_background_color=scheme.tab_active_background_color,
                             tab_active_color=scheme.tab_active_color,

                             tooltip_background_color=scheme.tooltip_background_color,
                             tooltip_text_color_label=scheme.tooltip_text_label_color,
                             tooltip_text_color_value=scheme.tooltip_text_value_color,
                             body_background_color=scheme.body_fill,
                             headline_color=scheme.plot_title_text_color,
                             text_color=scheme.text_color,
                           )
                      )
    return css

def get_nondefault_params(params):
    return {key: params._get(key) for key in params._getkeys() if not params.isdefault(key) and key != 'plotname'}


def get_params_str(params, number_format):
    user_params = get_nondefault_params(params)

    def get_value_str(name, value, number_format):
        if name == "timeframe":
            return bt.TimeFrame.getname(value, 1)
        elif isinstance(value, str):
            return value
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, list):
            return ','.join(value)
        else:
            format_str = number_format.split('.')
            if len(format_str) == 2:
                decimal_points = len(format_str[1])
            else:
                decimal_points = 2
            if isinstance(value, numbers.Number):
                return "{:.{}f}".format(value, decimal_points)
            else:
                return "{}".format(value)

    plabs = ["{}: {}".format(x, get_value_str(x, y, number_format)) for x, y in user_params.items()]
    plabs = ', '.join(plabs)
    return plabs


def get_strategy_label(strategycls, params, number_format):
    if strategycls is None:
        return get_params_str(params, number_format)
    else:
        label = strategycls.__name__
        plabs = get_params_str(params, number_format)
        return "{} [{}]".format(label, plabs)


def nanfilt(x):
    """filters all NaN values from a list"""
    return [value for value in x if not math.isnan(value)]


def resample_line(line, line_clk, new_clk):
    """Resamples data line to a new clock. Missing values will be filled with NaN."""
    if new_clk is None:
        return line

    new_line = []
    next_idx = len(line_clk) - 1
    for sc in new_clk:
        for i in range(next_idx, 0, -1):
            v = line_clk[-i]
            if sc == v:
                # exact hit
                new_line.append(line[-i])
                next_idx = i
                break
        else:
            new_line.append(float('nan'))
    return new_line


def convert_to_pandas(strat_clk, obj, start=None, end=None, name_prefix=""):
    df = pandas.DataFrame()
    for lineidx in range(obj.size()):
        line = obj.lines[lineidx]
        linealias = obj.lines._getlinealias(lineidx)
        if linealias == 'datetime':
            continue
        data = line.plotrange(start, end)

        ndata = resample_line(data, obj.lines.datetime.plotrange(start, end), strat_clk)
        logging.info("Filled_line: {}: {}".format(linealias, str(ndata)))

        df[name_prefix + linealias] = ndata

    df[name_prefix + 'datetime'] = [bt.num2date(x) for x in strat_clk]
    return df


def get_data_obj(ind):
    """obj can be a data object or just a single line (in case indicator was created with an explicit line)"""
    while True:
        if isinstance(ind, bt.LineSeriesStub):
            return ind.owner
        elif isinstance(ind, bt.Indicator):
            ind = ind.data
        else:
            return ind
