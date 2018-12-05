from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols = [['Time', ColummDataType.DATETIME],
            ['Ticker', ColummDataType.STRING],
            ['Size', ColummDataType.INT],
            ['Price', ColummDataType.FLOAT],
            ['Total Value', ColummDataType.FLOAT]
            ]

    for k, v in self.get_analysis().items():
        cols[0].append(k)
        cols[1].append(v[0][0])
        cols[2].append(v[0][1])
        cols[3].append(v[0][2])
        cols[4].append(v[0][3])

    return "Transactions", [cols]
