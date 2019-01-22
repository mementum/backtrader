import backtrader
import logging
from .drawdown import datatable as drawdown
from .timedrawdown import datatable as timedrawdown
from .sharperatio import datatable as sharperatio
from .tradeanalyzers import datatable as tradeanalyzer
from .tradedetails import datatable as tradedetails
from .transactions import datatable as transactions
from .calmar import datatable as calmar
from .annualreturn import datatable as annualreturn
from .returns import datatable as returns
from .leverage import datatable as leverage
from .vwr import datatable as vwr
from .timereturn import datatable as timereturn
from .sqn import datatable as sqn

_logger = logging.getLogger(__name__)
_DATATABLE_FNC_NAME = 'get_analysis_table'


def inject_datatables():
    """Injects function 'get_analysis_table' to some well-known Analyzer classes."""
    _atables = {
        backtrader.analyzers.sharpe.SharpeRatio: sharperatio,
        backtrader.analyzers.DrawDown: drawdown,
        backtrader.analyzers.TimeDrawDown: timedrawdown,
        backtrader.analyzers.TradeAnalyzer: tradeanalyzer,
        backtrader.analyzers.Transactions: transactions,
        backtrader.analyzers.Calmar: calmar,
        backtrader.analyzers.AnnualReturn: annualreturn,
        backtrader.analyzers.Returns: returns,
        backtrader.analyzers.GrossLeverage: leverage,
        backtrader.analyzers.VariabilityWeightedReturn: vwr,
        backtrader.analyzers.TimeReturn: timereturn,
        backtrader.analyzers.SQN: sqn,
        backtrader.analyzers.TradeDetails: tradedetails
    }

    for cls, labdict in _atables.items():
        curlab = getattr(cls, _DATATABLE_FNC_NAME, None)
        if curlab is not None:
            _logger.warning("Analyzer class '{}' already contains a function 'get_rets_table'. Not overriding.".format(cls.__name__))
            continue
        setattr(cls, _DATATABLE_FNC_NAME, labdict)
