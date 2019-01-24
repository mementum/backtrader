from ..datatable import ColummDataType


def datatable(self):
    cols = [['Name', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]
    cols[0].append('Sharpe-Ratio')

    a = self.get_analysis()
    cols[1].append(a['sharperatio'])

    name = "Sharpe Ratio"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols]
