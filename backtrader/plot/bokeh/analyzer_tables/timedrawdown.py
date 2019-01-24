from ..datatable import ColummDataType


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

    name = "Time Drawdown"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols1]

