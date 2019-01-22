from jinja2 import Environment, PackageLoader
import backtrader
import matplotlib.colors
from ..utils import nanfilt

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
    env = Environment(loader=PackageLoader('backtrader.boplot.bokeh', 'templates'))
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
