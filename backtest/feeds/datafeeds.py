"""
编写私有的数据文件类。
"""
from backtrader.feeds import GenericCSVData


class StockCsvData(GenericCSVData):
    params = (
        ('nullvalue', 0.0),
        ('dtformat', '%Y-%m-%d'),
        ('datetime', 1),
        ('open', 2),
        ('high', 4),
        ('low', 5),
        ('close', 3),
        ('volume', 6),
        ('openinterest', -1),
    )
