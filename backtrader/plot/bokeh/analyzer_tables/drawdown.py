from ..datatable import ColummDataType


def datatable(self):
    cols1 = [['Feature', ColummDataType.STRING], ['Value', ColummDataType.FLOAT], ['Maximum', ColummDataType.FLOAT]]

    a = self.get_analysis()
    cols1[0].append('Periods')
    cols1[1].append(a['len'])
    cols1[2].append(a['max']['len'])

    cols1[0].append('Moneydown ($)')
    cols1[1].append(a['moneydown'])
    cols1[2].append(a['max']['moneydown'])

    cols1[0].append('Drawdown (%)')
    cols1[1].append(a['drawdown'])
    cols1[2].append(a['max']['drawdown'])

    name = "Drawdown"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols1]

