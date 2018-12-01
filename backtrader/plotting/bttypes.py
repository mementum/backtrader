import backtrader as bt
from typing import Union, List, Dict, Any


BtResult = List[bt.Strategy]
OptResult = List[List[bt.OptReturn]]
OrderedOptResult = List[Dict[str, Any]]


def is_btresult(result: Union[BtResult, OptResult, OrderedOptResult]):
    return isinstance(result, List) and isinstance(result[0], bt.Strategy)


def is_optresult(result: Union[BtResult, OptResult, OrderedOptResult]):
    return isinstance(result, List) and isinstance(result[0], List) and len(result[0]) > 0 and isinstance(result[0][0], (bt.OptReturn, bt.Strategy))


def is_ordered_optresult(result: Union[BtResult, OptResult, OrderedOptResult]):
    return isinstance(result, dict) and isinstance(result['optresult'][0], Dict)


def is_valid_result(result: List):
    """Raises if result is not a list. Return False if result is empty."""
    val_fncs = [is_btresult, is_optresult, is_ordered_optresult]
    if not any([x(result) for x in val_fncs]):
        raise Exception("'result' is not a valid result object")
    return len(result) != 0
