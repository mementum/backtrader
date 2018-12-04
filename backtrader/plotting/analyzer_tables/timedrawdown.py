from backtrader.plotting.bokeh.datatable import ColummDataType


def datatable(self):
    cols1 = [['Feature', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()
    if 'drawdown' in a:
      cols1[0].append('DrawDown (%)')
      cols1[1].append(a['drawdown'])

    cols1[0].append('Max DrawDown (%)')
    cols1[1].append(a['maxdrawdown'])

    cols1[0].append('Max DrawDown Period')
    cols1[1].append(a['maxdrawdownperiod'])

    return "TimeDrawDown", [cols1]

