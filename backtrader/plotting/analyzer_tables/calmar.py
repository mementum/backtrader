from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols1 = [['DateTime', ColummDataType.DATETIME], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()

    for k, v in a.items():
        cols1[0].append(k)
        cols1[1].append(v)

    return "Calmar", [cols1]

