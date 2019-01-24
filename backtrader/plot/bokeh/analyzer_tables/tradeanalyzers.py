from ..datatable import ColummDataType


def datatable(self):
    def gdef(obj, attr, d):
        return obj[attr] if attr in obj else d

    a = self.get_analysis()
    tables = []

    tab1 = [['', ColummDataType.STRING], ['Total', ColummDataType.INT], ['Open', ColummDataType.INT], ['Closed', ColummDataType.INT]]
    tab1[0].append('Number of Trades')
    tab1[1].append(a['total']['total'])
    if 'open' in a['total']:
        tab1[2].append(a['total']['open'])
    else:
        tab1[2].append('-')
    tab1[3].append(gdef(a['total'], 'closed', 0))
    tables.append(tab1)

    if 'streak' in a and 'pnl' in a:
        tab2 = [['Streak', ColummDataType.STRING], ['Current', ColummDataType.INT], ['Longest', ColummDataType.INT]]
        tab2[0].append('Won')
        tab2[1].append(a['streak']['won']['current'])
        tab2[2].append(a['streak']['won']['longest'])

        tab2[0].append('Lost')
        tab2[1].append(a['streak']['lost']['current'])
        tab2[2].append(a['streak']['lost']['longest'])

        tables.append(tab2)

        tab3 = [['Profit & Loss', ColummDataType.STRING], ['Total', ColummDataType.FLOAT], ['Average', ColummDataType.FLOAT]]
        tab3[0].append('Gross Profit')
        tab3[1].append(a['pnl']['gross']['total'])
        tab3[2].append(a['pnl']['gross']['average'])

        tab3[0].append('Net Profit (w/ Commissions)')
        tab3[1].append(a['pnl']['net']['total'])
        tab3[2].append(a['pnl']['net']['average'])

        tab3[0].append('Short')
        tab3[1].append(a['short']['pnl']['total'])
        tab3[2].append(a['short']['pnl']['average'])

        tab3[0].append('Long')
        tab3[1].append(a['long']['pnl']['total'])
        tab3[2].append(a['long']['pnl']['average'])

        tab3[0].append('Won / Short')
        tab3[1].append(a['short']['pnl']['won']['total'])
        tab3[2].append(a['short']['pnl']['won']['average'])

        tab3[0].append('Lost / Short')
        tab3[1].append(a['short']['pnl']['lost']['total'])
        tab3[2].append(a['short']['pnl']['lost']['average'])

        tab3[0].append('Won / Long')
        tab3[1].append(a['long']['pnl']['won']['total'])
        tab3[2].append(a['long']['pnl']['won']['average'])

        tab3[0].append('Lost / Long')
        tab3[1].append(a['long']['pnl']['lost']['total'])
        tab3[2].append(a['long']['pnl']['lost']['average'])

        tables.append(tab3)

        # tab4 = [['Long', ColummDataType.STRING], ['Gross', ColummDataType.FLOAT], ['Net', ColummDataType.FLOAT]]
        # tab4[0].append('Longest')
        # tab4[1].append(a['streak']['won']['longest'])
        # tab4[2].append(a['streak']['lost']['longest'])
        # tables.append(tab4)

        tab5 = [['Trades', ColummDataType.STRING], ['Total', ColummDataType.INT], ['Won', ColummDataType.INT], ['Lost', ColummDataType.INT], ['% Won', ColummDataType.INT]]
        tab5[0].append('Long')
        tab5[1].append(a['long']['total'])
        tab5[2].append(a['long']['won'])
        tab5[3].append(a['long']['lost'])
        tab5[4].append((a['long']['won'] / a['long']['total'] if a['long']['total'] else 0) * 100)

        tab5[0].append('Short')
        tab5[1].append(a['short']['total'])
        tab5[2].append(a['short']['won'])
        tab5[3].append(a['short']['lost'])
        tab5[4].append((a['short']['won'] / a['short']['total'] if a['short']['total'] else 0) * 100)

        tab5[0].append('All')
        tab5[1].append(a['won']['total'] + a['lost']['total'])
        tab5[2].append(a['won']['total'])
        tab5[3].append(a['lost']['total'])
        tab5[4].append((a['won']['total'] / (a['won']['total'] + a['lost']['total']) if (a['won']['total'] + a['lost']['total']) else 0) * 100)

        # tab5[0].append('All')
        # tab5[1].append(a['won']['total'] + a['lost']['total'])
        # tab5[2].append(a['won']['total'])
        # tab5[3].append(a['lost']['total'])

        tables.append(tab5)

        tab_len = [['Trade Length', ColummDataType.STRING], ['Total', ColummDataType.INT], ['Min', ColummDataType.INT], ['Max', ColummDataType.INT], ['Average', ColummDataType.FLOAT]]
        tab_len[0].append('Won')
        tab_len[1].append(a['len']['won']['total'])
        if 'min' in a['len']['won']:
            tab_len[2].append(a['len']['won']['min'])
        else:
            tab_len[2].append(float('nan'))
        tab_len[3].append(a['len']['won']['max'])
        tab_len[4].append(a['len']['won']['average'])

        tab_len[0].append('Lost')
        tab_len[1].append(a['len']['lost']['total'])
        if 'min' in a['len']['lost']:
            tab_len[2].append(a['len']['lost']['min'])
        else:
            tab_len[2].append(float('nan'))
        tab_len[3].append(a['len']['lost']['max'])
        tab_len[4].append(a['len']['lost']['average'])

        tab_len[0].append('Long')
        tab_len[1].append(a['len']['long']['total'])
        tab_len[2].append(a['len']['long']['min'])
        tab_len[3].append(a['len']['long']['max'])
        tab_len[4].append(a['len']['long']['average'])

        tab_len[0].append('Short')
        tab_len[1].append(a['len']['short']['total'])
        tab_len[2].append(a['len']['short']['min'])
        tab_len[3].append(a['len']['short']['max'])
        tab_len[4].append(a['len']['short']['average'])

        tab_len[0].append('Won / Long')
        tab_len[1].append(a['len']['long']['won']['total'])
        tab_len[2].append(a['len']['long']['won']['min'])
        tab_len[3].append(a['len']['long']['won']['max'])
        tab_len[4].append(a['len']['long']['won']['average'])

        tab_len[0].append('Won / Short')
        tab_len[1].append(a['len']['short']['won']['total'])
        tab_len[2].append(a['len']['short']['won']['min'])
        tab_len[3].append(a['len']['short']['won']['max'])
        tab_len[4].append(a['len']['short']['won']['average'])

        tab_len[0].append('Lost / Long')
        tab_len[1].append(a['len']['long']['lost']['total'])
        tab_len[2].append(a['len']['long']['lost']['min'])
        tab_len[3].append(a['len']['long']['lost']['max'])
        tab_len[4].append(a['len']['long']['lost']['average'])

        tab_len[0].append('Lost / Short')
        tab_len[1].append(a['len']['short']['lost']['total'])
        tab_len[2].append(a['len']['short']['lost']['min'])
        tab_len[3].append(a['len']['short']['lost']['max'])
        tab_len[4].append(a['len']['short']['lost']['average'])

        tables.append(tab_len)

    name = "Transaction Analyzer"
    if self.p.plotname:
        name = self.p.plotname

    return name, tables

