from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols1 = [['Feature', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()
    if 'drawdown' in a:
      cols1[0].append('Drawdown (%)')
      cols1[1].append(a['drawdown'])

    cols1[0].append('Max Drawdown (%)')
    cols1[1].append(a['maxdrawdown'])

    cols1[0].append('Max Drawdown Period')
    cols1[1].append(a['maxdrawdownperiod'])

    return "Time Drawdown", [cols1]

