import backtrader as bt
from typing import Dict, Optional, List, Union
import math
from datetime import datetime
import pandas
import logging


_logger = logging.getLogger(__name__)


def get_nondefault_params(params: object) -> Dict[str, object]:
    return {key: params._get(key) for key in params._getkeys() if not params.isdefault(key)}


def get_params_str(params: Optional[bt.AutoInfoClass]) -> str:
    user_params = get_nondefault_params(params)

    def get_value_str(name, value):
        if name == "timeframe":
            return bt.TimeFrame.getname(value, 1)
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, list):
            return ','.join(value)
        else:
            return f"{value:.2f}"

    plabs = [f"{x}: {get_value_str(x, y)}" for x, y in user_params.items()]
    plabs = '/'.join(plabs)
    return plabs


def get_strategy_label(strategycls: bt.MetaStrategy, params: Optional[bt.AutoInfoClass]) -> str:
    label = strategycls.__name__
    plabs = get_params_str(params)
    return f'{label} [{plabs}]'


def nanfilt(x: List) -> List:
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


def convert_to_pandas(strat_clk, obj: bt.LineSeries, start: datetime=None, end: datetime=None, name_prefix: str="") -> pandas.DataFrame:
    df = pandas.DataFrame()
    for lineidx in range(obj.size()):
        line = obj.lines[lineidx]
        linealias = obj.lines._getlinealias(lineidx)
        if linealias == 'datetime':
            continue
        data = line.plotrange(start, end)

        ndata = resample_line(data, obj.lines.datetime.plotrange(start, end), strat_clk)
        logging.info(f"Filled_line: {linealias}: {str(ndata)}")

        df[name_prefix + linealias] = ndata

    df[name_prefix + 'datetime'] = [bt.num2date(x) for x in strat_clk]
    return df


def get_data_obj(ind: Union[bt.Indicator, bt.LineSeriesStub]):
    """obj can be a data object or just a single line (in case indicator was created with an explicit line)"""
    while True:
        if isinstance(ind, bt.LineSeriesStub):
            return ind.owner
        elif isinstance(ind, bt.Indicator):
            ind = ind.data
        else:
            return ind
