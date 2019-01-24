from ..datatable import ColummDataType

def datatable(self):
    cols = [['Ref', ColummDataType.INT],
            ['Ticker', ColummDataType.STRING],
            ['Position', ColummDataType.STRING],
            ['Periods', ColummDataType.INT],
            ['TimeIn', ColummDataType.DATETIME],
            ['TimeOut', ColummDataType.DATETIME],
            ['PNL', ColummDataType.FLOAT],
            ['CPNL', ColummDataType.FLOAT],
            ['MFE%', ColummDataType.FLOAT],
            ['MAE%', ColummDataType.FLOAT],
            ]

    for k, v in self.get_analysis().items():
        cols[0].append(k)
        cols[1].append(v[0][0])
        cols[2].append(v[0][1])
        cols[3].append(v[0][2])
        cols[4].append(v[0][3])
        cols[5].append(v[0][4])
        cols[6].append(v[0][5])
        cols[7].append(v[0][6])
        cols[8].append(v[0][7])
        cols[9].append(v[0][8])
        # cols[10].append(v[0][9])

    name = "Trade Details"
    if self.p.plotname:
        name = self.p.plotname

    return name, [cols]
