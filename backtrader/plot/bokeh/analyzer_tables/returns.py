from ..datatable import ColummDataType


def datatable(self):
    cols1 = [['Feature', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()
    cols1[0].append('Total Compound Return (%)')
    cols1[1].append(round(a['rtot']*100, 2))

    cols1[0].append('Average Return (%)')
    cols1[1].append(round(a['ravg']*100, 2))

    cols1[0].append('Annualized Return (%)')
    cols1[1].append(round(a['rnorm100'], 2))

    name = "Returns"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols1]

