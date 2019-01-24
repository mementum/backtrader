from ..datatable import ColummDataType


def datatable(self):
    cols1 = [['DateTime', ColummDataType.DATETIME], ['Return', ColummDataType.FLOAT]]

    a = self.get_analysis()

    for k, v in a.items():
        cols1[0].append(k)
        cols1[1].append(v)

    name = "Time Return"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols1]

