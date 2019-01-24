from ..datatable import ColummDataType


def datatable(self):
    cols1 = [['Name', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()
    cols1[0].append('SystemQualityNumber')
    cols1[1].append(a['sqn'])

    cols1[0].append('Trades')
    cols1[1].append(a['trades'])

    name = "System Quality Number"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols1]

