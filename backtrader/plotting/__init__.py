try:
    from .bokeh.bokeh import Bokeh
except ImportError as e:
    raise ImportError(
        'Bokeh seems to be missing. Needed for plotting support')

# initialize analyzer tables
from backtrader.plotting.analyzer_tables import inject_datatables
inject_datatables()
