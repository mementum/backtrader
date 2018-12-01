from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols = [['Time', ColummDataType.DATETIME],
            # ['Data ID', ColummDataType.INT],
            ['Size', ColummDataType.INT],
            ['Price', ColummDataType.FLOAT],
            ['Ticker', ColummDataType.STRING],
            ['Total Value', ColummDataType.FLOAT]
            ]

    # size, price, i, dname, -size * price
    for k, v in self.get_analysis().items():
        cols[0].append(k)
        # cols[1].append(v[0][2])
        cols[1].append(v[0][0])
        cols[2].append(v[0][1])
        cols[3].append(v[0][3])
        cols[4].append(v[0][4])

    return "Transactions", [cols]
