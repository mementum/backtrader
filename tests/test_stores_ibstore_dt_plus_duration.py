import backtrader as bt
import datetime as dt

store = bt.stores.IBStore()


def test_run():

    test_cases = [
                (dt.datetime(2020, 7, 31), '2 M', dt.datetime(2020, 10, 1)),
                (dt.datetime(2020, 12, 29), '2 M', dt.datetime(2021, 3, 1)),
                (dt.datetime(2020, 12, 30), '2 M', dt.datetime(2021, 3, 2)),
                (dt.datetime(2020, 12, 31), '2 M', dt.datetime(2021, 3, 3)),
                (dt.datetime(2019, 12, 29), '2 M', dt.datetime(2020, 2, 29)),
                (dt.datetime(2019, 12, 30), '2 M', dt.datetime(2020, 3, 1)),
                (dt.datetime(2019, 12, 31), '2 M', dt.datetime(2020, 3, 2)),
                (dt.datetime(1999, 12, 31), '2 M', dt.datetime(2000, 3, 2)),
                (dt.datetime(2099, 12, 31), '2 M', dt.datetime(2100, 3, 3))
                ]
    for src_dt, duration_str, trg_dt in test_cases:
        calculated_dt = store.dt_plus_duration(src_dt, duration_str)
        assert calculated_dt == trg_dt


if __name__ == '__main__':
    test_run()
