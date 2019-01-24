from ..datatable import ColummDataType


def datatable(self):
    cols1 = [['Name', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()
    cols1[0].append('VWR')
    cols1[1].append(a['vwr'])

    name = "Variability-Weighted Return"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols1]

