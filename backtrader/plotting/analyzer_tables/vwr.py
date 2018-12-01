from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols1 = [['Name', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()
    cols1[0].append('VWR')
    cols1[1].append(a['vwr'])

    return "Variability-Weighted Return", [cols1]

