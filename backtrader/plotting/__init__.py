try:
    from .bokeh.bokeh import Bokeh
except ImportError as e:
    pass

# initialize analyzer tables
from backtrader.plotting.analyzer_tables import inject_datatables
inject_datatables()
