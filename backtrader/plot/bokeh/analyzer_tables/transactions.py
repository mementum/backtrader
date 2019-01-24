from ..datatable import ColummDataType

# self.rets[self.strategy.datetime.datetime().replace(tzinfo=self.strategy.data._tz)] = entries
# 'date', 'size', 'amount', 'price', 'sid', 'symbol', 'value'
def datatable(self):
    cols = [['Time', ColummDataType.DATETIME],
            ['Ticker', ColummDataType.STRING],
            ['Size', ColummDataType.INT],
            ['Price', ColummDataType.FLOAT],
            ['Total Value', ColummDataType.FLOAT]
            ]

    for k, v in self.get_analysis().items():
        cols[0].append(k)
        cols[1].append(v[0][3])
        cols[2].append(v[0][0])
        cols[3].append(v[0][1])
        cols[4].append(v[0][4])

    name = "Transactions"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols]
