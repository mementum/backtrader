from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols1 = [['Year', ColummDataType.STRING], ['Return', ColummDataType.FLOAT]]

    a = self.get_analysis()

    for k, v in a.items():
        cols1[0].append(k)
        cols1[1].append(v)

    return "Annual Return", [cols1]

