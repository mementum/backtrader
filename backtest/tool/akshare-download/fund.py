import os

import akshare as ak

mainpath = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
mainpath = os.path.join(mainpath, 'datas/fund')

'''
Get funds datas
'''
def get_all_fund_list():
    """
    Get all fund name list
    """
    fund_em_fund_name_df = ak.fund_em_fund_name()
    path = os.path.join(mainpath, f'all_fund.csv')
    fund_em_fund_name_df.to_csv(path)


def get_etf_list():
    """
    Get all ETF fund name list
    """
    fund_list = ak.fund_etf_category_sina(symbol="ETF基金")
    path = os.path.join(mainpath, f'etf_list.csv')
    fund_list.to_csv(path, encoding='utf-8')


def get_lof_list():
    """
    Get all LOF fund name list
    """
    fund_list = ak.fund_etf_category_sina(symbol="LOF基金")
    path = os.path.join(mainpath, f'lof_list.csv')
    fund_list.to_csv(path, encoding='utf-8')

def get_fund_detail(etf_fund_code, down_path=''):
    """
    Get fund data
    """
    fund_detail = ak.fund_etf_hist_sina(symbol=etf_fund_code)
    path = ''
    if down_path == '':
        path = os.path.join(mainpath, f'{etf_fund_code}.csv')
    if down_path == 'etfs':
        path = os.path.join(mainpath, f'etfs/{etf_fund_code}.csv')
    if down_path == 'lofs':
        path = os.path.join(mainpath, f'lofs/{etf_fund_code}.csv')

    fund_detail['fundname'] = etf_fund_code
    fund_detail.to_csv(path, encoding='utf-8')


def get_open_fund_info(fund_code):
    """
    Get open fund info
    """
    fund_data = ak.fund_em_open_fund_info(fund=fund_code, indicator="单位净值走势")
    fund_data_new = fund_data.rename(columns={
        '净值日期': 'datetime',
        '单位净值': 'open',
        '日增长率': 'rate',
    })
    result_data = fund_data_new[['datetime', 'open', 'rate']]
    path = os.path.join(mainpath, f'{fund_code}.csv')
    result_data.to_csv(path, index=None, encoding='utf-8')


def download_open_fund():
    """
    广发多因子混合 002943
    广发价值领先混合 008099
    富国中证 500 指数 161017
    """
    fund_list = ['161017', '002943', '008099']
    for fund in fund_list:
        get_open_fund_info(fund_code=fund)


def download_etf_fund():
    """
    sh513050 中概互联
    sz159992 创新药

    sz159952 创业etf
    sh510500 500etf
    sz159949 创业板 50
    sh510310 沪深300

    sz159915 创业板
    sh518880 黄金ETF
    sh513100 纳指ETF
    """
    funds = [
        'sh513050', 'sz159992', 'sz159952', 'sh510500', 'sz159949', 'sh510310',
        'sz159915', 'sh518880', 'sh513100'
    ]
    for fund in funds:
        get_fund_detail(fund)


def name_list(csv_name):
    import csv
    csv_f = os.path.join(mainpath, f'{csv_name}')
    fund_list = []
    with open(csv_f, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['name'].startswith('N'):
                fund_list.append(row['symbol'])
            else:
                print(row['name'])
    return fund_list


def download_all_fund(csv_name, down_path=''):

    from progress.bar import IncrementalBar

    fund_list = name_list(csv_name)

    bar = IncrementalBar('Download', max=len(fund_list))
    new_fund_list = []
    for fund in fund_list:
        bar.next()
        try:
            get_fund_detail(fund, down_path)
        except KeyError:
            new_fund_list.append(fund)

        bar.finish()

    if len(new_fund_list) > 0:
        print(f'新基金有: {new_fund_list}')


if __name__ == '__main__':
    #get_all_fund_list()
    # get_etf_list()
    # get_lof_list()

    # download_etf_fund()
    # download_open_fund()

    download_all_fund('etf_list.csv', 'etfs')
    download_all_fund('lof_list.csv', 'lofs')