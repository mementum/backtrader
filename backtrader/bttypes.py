import backtrader as bt

class OptReturn(object):
    def __init__(self, params, **kwargs):
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)

class OrderedOptResult:
    """Class to store an optresult which has been evaluated by a benchmark. The benchmark has a name (`benchmark_label`)."""
    class BenchmarkedResult:
        def __init__(self, benchmark, result):
            self.benchmark = benchmark
            self.result = result

    def __init__(self, benchmark_label, optresult):
        self.benchmark_label = benchmark_label
        self.optresult = optresult


def is_btresult(result):
    return isinstance(result, list) and isinstance(result[0], bt.Strategy) and len(result) > 0


def is_optresult(result):
    return isinstance(result, list) and \
           isinstance(result[0], list) and \
           len(result[0]) > 0 and \
           isinstance(result[0][0], (OptReturn, bt.Strategy)) and \
           len(result) > 0


def is_ordered_optresult(result):
    return isinstance(result, OrderedOptResult)