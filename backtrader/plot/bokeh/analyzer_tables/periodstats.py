from ..datatable import ColummDataType


def datatable(self):
    table1 = [['Name', ColummDataType.STRING], ['Value', ColummDataType.FLOAT]]

    a = self.get_analysis()

    table1[0].append("Average")
    table1[1].append(a.average)

    table1[0].append("Standard Deviation")
    table1[1].append(a.stddev)

    table1[0].append("Positive #")
    table1[1].append(a.positive)

    table1[0].append("Negative #")
    table1[1].append(a.negative)

    table1[0].append("Neutral #")
    table1[1].append(a.nochange)

    table1[0].append("Best")
    table1[1].append(a.best)

    table1[0].append("Worst")
    table1[1].append(a.worst)

    name = "Period Stats"
    if self.p.plotname:
        name = self.p.plotname

    return name, [table1]

