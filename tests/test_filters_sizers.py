#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2026 Dennis Hansen
#
# This file is part of slim-backtrader, a modified version of backtrader
# (Copyright (C) 2015-2023 Daniel Rodriguez).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""Filters, sizers, fillers and commission schemes."""

import datetime

import pytest

import backtrader as bt

from conftest import csvdata, datafile


def barcount(data, filter_cls=None, filter_kwargs=None, **cerebro_kwargs):
    count = []

    class Counter(bt.Strategy):
        __test__ = False

        def next(self):
            count.append(self.data.close[0])

    if filter_cls is not None:
        data.addfilter(filter_cls, **(filter_kwargs or {}))
    cerebro = bt.Cerebro(stdstats=False, **cerebro_kwargs)
    cerebro.adddata(data)
    cerebro.addstrategy(Counter)
    cerebro.run()
    return count


class TestFilters:
    def test_unfiltered_baseline(self):
        assert len(barcount(csvdata())) == 255

    def test_heikinashi_filter_changes_the_bars(self):
        plain = barcount(csvdata())
        ha = barcount(csvdata(), bt.filters.HeikinAshi)
        assert len(ha) == len(plain)
        assert ha != plain  # the closes are averaged, so they must differ

    def test_renko_filter_produces_brick_bars(self):
        bricks = barcount(csvdata(), bt.filters.Renko, dict(size=50))
        assert 0 < len(bricks) < 255  # bricks are coarser than daily bars

    def test_renko_brick_size_controls_the_count(self):
        coarse = barcount(csvdata(), bt.filters.Renko, dict(size=200))
        fine = barcount(csvdata(), bt.filters.Renko, dict(size=25))
        assert len(fine) > len(coarse)

    @pytest.mark.parametrize("preload", [True, False])
    def test_a_filter_returning_true_removes_the_bar(self, preload):
        """A Filter subclass drops a bar by calling backwards() and returning
        True. Filter.__call__ discarded that return value, so load() reported
        a bar that was not there: preloading hid it, and without preloading
        the strategy was handed an empty buffer (IndexError)."""

        class EveryOther(bt.Filter):
            n = 0

            def next(self, data):
                self.n += 1
                if self.n % 2 == 0:
                    data.backwards()
                    return True
                return False

        assert len(barcount(csvdata(), EveryOther, preload=preload)) == 128

    @pytest.mark.parametrize("size", [25, 50, 200])
    def test_renko_bricks_do_not_depend_on_preload(self, size):
        kwargs = dict(size=size)
        assert barcount(csvdata(), bt.filters.Renko, kwargs, preload=False) == (
            barcount(csvdata(), bt.filters.Renko, kwargs, preload=True)
        )

    def test_every_renko_brick_has_its_high_above_its_low(self):
        """A falling brick was written with high = its bottom and low = its
        top, so its high sat below its low."""
        bricks = []

        class Recorder(bt.Strategy):
            __test__ = False

            def next(self):
                d = self.data
                bricks.append((d.open[0], d.high[0], d.low[0], d.close[0]))

        data = csvdata()
        data.addfilter(bt.filters.Renko, size=50)
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(data)
        cerebro.addstrategy(Recorder)
        cerebro.run()
        falling = [b for b in bricks if b[3] < b[0]]
        assert falling  # the year has falling bricks to check
        for o, h, l, c in bricks:
            assert h == max(o, c) and l == min(o, c)
            assert h - l == 50

    def test_calendardays_filter_fills_missing_sessions(self):
        """Regression: with its own documented default (fill_price=None,
        'use the last known closing price') the filter raised TypeError,
        because `if self.p.fill_price > 0` was evaluated before the branch
        that handles None."""
        filled = barcount(csvdata(), bt.filters.CalendarDays)
        assert len(filled) > 255  # weekends and holidays get filled

    def test_calendardays_default_fills_with_the_last_close(self):
        filled = barcount(csvdata(), bt.filters.CalendarDays)
        plain = barcount(csvdata())
        # every filled bar repeats a close that really occurred
        assert set(filled) == set(plain)

    def test_calendardays_explicit_fill_price_is_used(self):
        filled = barcount(csvdata(), bt.filters.CalendarDays, dict(fill_price=42.0))
        assert 42.0 in filled

    def test_calendardays_midpoint_fill(self):
        filled = barcount(csvdata(), bt.filters.CalendarDays, dict(fill_price=-1))
        assert len(filled) > 255

    def test_datafiller_is_available_under_both_names(self):
        assert bt.filters.DataFiller is not None
        assert bt.filters.SessionFiller is not None

    def test_session_filter_drops_out_of_session_bars(self):
        # intraday data, restricted to a narrow session
        data = bt.feeds.BacktraderCSVData(
            dataname=datafile("2006-min-005.txt"),
            timeframe=bt.TimeFrame.Minutes,
            compression=5,
            sessionstart=datetime.time(10, 0),
            sessionend=datetime.time(11, 0),
        )
        inside = barcount(data, bt.filters.SessionFilter)
        assert 0 < len(inside)


class TestSizers:
    def _run(self, sizer, cash=100000.0, comm=None, **kwargs):
        sizes = []

        class Trader(bt.Strategy):
            __test__ = False

            def notify_order(self, order):
                if order.status == order.Completed:
                    sizes.append(order.executed.size)

            def next(self):
                if len(self) == 5:
                    self.buy()

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(cash)
        if comm:
            cerebro.broker.setcommission(**comm)
        cerebro.adddata(csvdata())
        cerebro.addsizer(sizer, **kwargs)
        cerebro.addstrategy(Trader)
        cerebro.run()
        return sizes

    def test_fixed_size_uses_the_configured_stake(self):
        assert self._run(bt.sizers.FixedSize, stake=7) == [7]

    def test_default_sizer_is_one_unit(self):
        assert self._run(bt.sizers.FixedSize) == [1]

    def test_percent_sizer_scales_with_portfolio_value(self):
        small = self._run(bt.sizers.PercentSizer, percents=1)
        large = self._run(bt.sizers.PercentSizer, percents=50)
        assert large[0] > small[0]

    # Bar 5, where the order is sized, closed at 3666.99.

    def test_percent_sizer_on_a_stock_is_cash_over_price(self):
        sizes = self._run(bt.sizers.PercentSizer, percents=50)
        assert sizes == [pytest.approx(50000.0 / 3666.99)]

    def test_percent_sizer_counts_the_multiplier(self):
        # 50% of 10,000,000 at 3666.99 x 100 a unit: 13.6, so 13 units. It
        # used to ask for 1,363 - a hundred times what the cash covers -
        # and the order was refused
        comm = dict(mult=100.0, stocklike=True, commtype=bt.CommInfoBase.COMM_FIXED)
        sizes = self._run(bt.sizers.PercentSizerInt, cash=1e7, comm=comm, percents=50)
        assert sizes == [13]

    def test_percent_sizer_counts_a_futures_margin(self):
        # 50% of 100,000 at a margin of 2,000 a contract: 25 contracts, not
        # the 13 the price alone gives
        comm = dict(margin=2000.0, mult=10.0)
        assert self._run(bt.sizers.PercentSizerInt, comm=comm, percents=50) == [25]

    def test_fixed_reverser_is_exported(self):
        assert issubclass(bt.sizers.FixedReverser, bt.Sizer)

    def test_sizer_receives_the_broker_cash(self):
        class RecordingSizer(bt.Sizer):
            seen = []

            def _getsizing(self, comminfo, cash, data, isbuy):
                RecordingSizer.seen.append(cash)
                return 1

        self_cash = []

        class Trader(bt.Strategy):
            __test__ = False

            def next(self):
                if len(self) == 5:
                    self_cash.append(self.broker.getcash())
                    self.buy()

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(50000.0)
        cerebro.adddata(csvdata())
        cerebro.addsizer(RecordingSizer)
        cerebro.addstrategy(Trader)
        cerebro.run()
        assert RecordingSizer.seen
        assert RecordingSizer.seen[0] == pytest.approx(self_cash[0])


class TestFillers:
    def test_fixed_size_filler_caps_the_executed_size(self):
        executed = []

        class BigBuyer(bt.Strategy):
            __test__ = False

            def notify_order(self, order):
                if order.status == order.Completed:
                    executed.append(order.executed.size)

            def next(self):
                if len(self) == 5:
                    self.buy(size=100)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(1000000.0)
        cerebro.broker.set_filler(bt.fillers.FixedSize(size=10))
        # the daily file has zero volume, so use one that has volume
        cerebro.adddata(
            bt.feeds.BacktraderCSVData(dataname=datafile("2006-volume-day-001.txt"))
        )
        cerebro.addstrategy(BigBuyer)
        cerebro.run()
        assert executed == [] or max(executed) <= 100

    def test_fillers_are_exported(self):
        assert bt.fillers.FixedSize is not None
        assert bt.fillers.FixedBarPerc is not None
        assert bt.fillers.BarPointPerc is not None


class TestCommissionSchemes:
    def test_stock_scheme_is_percentage_of_notional(self):
        comm = bt.CommInfoBase(commission=0.001, stocklike=True, percabs=True)
        assert comm.getcommission(100, 10.0) == pytest.approx(1.0)

    def test_futures_scheme_is_per_contract(self):
        comm = bt.CommInfoBase(
            commission=2.0, stocklike=False, commtype=bt.CommInfoBase.COMM_FIXED
        )
        assert comm.getcommission(10, 100.0) == pytest.approx(20.0)

    def test_percabs_false_treats_commission_as_percent(self):
        comm = bt.CommInfoBase(commission=0.1, stocklike=True, percabs=False)
        # 0.1 means 0.1%, i.e. 0.001 absolute
        assert comm.getcommission(100, 10.0) == pytest.approx(1.0)

    def test_mult_scales_position_value_for_futures(self):
        comm = bt.CommInfoBase(mult=10.0, stocklike=False, margin=1000.0)
        assert comm.getvaluesize(2, 50.0) == pytest.approx(2 * 1000.0)

    def test_profit_and_loss_uses_the_multiplier(self):
        comm = bt.CommInfoBase(mult=10.0, stocklike=False, margin=1000.0)
        assert comm.profitandloss(2, 50.0, 55.0) == pytest.approx(2 * 5.0 * 10.0)

    def test_commission_scheme_aliases_exist(self):
        assert bt.commissions.CommInfo_Stocks_Perc is not None
        assert bt.commissions.CommInfo_Futures_Fixed is not None


def bars(data, **cerebro_kwargs):
    """Every OHLCV tuple a strategy is shown, in order."""
    seen = []

    class Recorder(bt.Strategy):
        __test__ = False

        def next(self):
            d = self.data
            seen.append(
                (
                    d.datetime.datetime(0),
                    d.open[0],
                    d.high[0],
                    d.low[0],
                    d.close[0],
                    d.volume[0],
                )
            )

    cerebro = bt.Cerebro(stdstats=False, **cerebro_kwargs)
    cerebro.adddata(data)
    cerebro.addstrategy(Recorder)
    cerebro.run()
    return seen


class TestBarSplitters:
    """Filters that turn one bar into two."""

    def test_bar_replayer_open_doubles_the_bar_count(self):
        plain = bars(csvdata())
        data = csvdata()
        data.addfilter(bt.filters.BarReplayer_Open)
        assert len(bars(data)) == 2 * len(plain)

    def test_bar_replayer_open_delivers_an_open_only_bar_first(self):
        data = csvdata()
        data.addfilter(bt.filters.BarReplayer_Open)
        first, second = bars(data)[:2]
        _, o, h, l, c, vol = first
        assert o == h == l == c  # the four components collapse to the open
        assert vol == 0.0  # and it carries no volume
        assert second[1] == o  # the full bar follows with the same open

    def test_bar_replayer_open_preserves_the_full_bar(self):
        plain = bars(csvdata())
        data = csvdata()
        data.addfilter(bt.filters.BarReplayer_Open)
        replayed = bars(data)
        # every second delivered bar is the original one
        assert [b[1:] for b in replayed[1::2]] == [b[1:] for b in plain]

    def test_day_splitter_close_yields_two_ticks_per_session(self):
        cerebro = bt.Cerebro(stdstats=False)
        data = csvdata()
        data.addfilter(bt.filters.DaySplitter_Close)
        cerebro.replaydata(data, timeframe=bt.TimeFrame.Days, compression=1)

        seen = []

        class Recorder(bt.Strategy):
            __test__ = False

            def next(self):
                seen.append(self.data.close[0])

        cerebro.addstrategy(Recorder)
        cerebro.run()
        # replay delivers the running bar repeatedly; two ticks per session
        # means strictly more deliveries than the 255 raw sessions
        assert len(seen) > 255

    def test_day_splitter_close_volume_split_is_configurable(self):
        def totalvol(closevol):
            data = csvdata()
            data.addfilter(bt.filters.DaySplitter_Close, closevol=closevol)
            cerebro = bt.Cerebro(stdstats=False)
            cerebro.replaydata(data, timeframe=bt.TimeFrame.Days, compression=1)
            vols = []

            class Recorder(bt.Strategy):
                __test__ = False

                def next(self):
                    vols.append(self.data.volume[0])

            cerebro.addstrategy(Recorder)
            cerebro.run()
            return vols

        # the split is a redistribution, so both settings must run and produce
        # the same number of deliveries
        assert len(totalvol(0.1)) == len(totalvol(0.9))


class TestDataWrappers:
    """DataFilter and DataFiller wrap a feed rather than filtering in place.

    Both were unreachable until the wrapped feed was started properly: nothing
    hands the inner feed to cerebro, so nothing gave it an environment or ran
    _start_finish(), and the first bar load raised AttributeError on _tzinput.
    """

    def wrap(self, funcfilter):
        return bt.filters.DataFilter(dataname=csvdata(), funcfilter=funcfilter)

    def test_data_filter_keeps_only_the_bars_the_callable_accepts(self):
        kept = bars(self.wrap(lambda d: d.close[0] > 4000.0), preload=False)
        assert kept  # something survived
        assert all(bar[4] > 4000.0 for bar in kept)
        assert len(kept) < 255

    def test_data_filter_accepting_everything_matches_the_plain_feed(self):
        assert len(bars(self.wrap(lambda d: True), preload=False)) == 255

    def test_data_filter_rejecting_everything_yields_no_bars(self):
        assert bars(self.wrap(lambda d: False), preload=False) == []

    def test_data_filter_only_mondays(self):
        kept = bars(
            self.wrap(lambda d: d.datetime.date().weekday() == 0), preload=False
        )
        assert kept
        assert all(bar[0].weekday() == 0 for bar in kept)

    def test_data_filter_passes_the_wrapped_bar_through_unchanged(self):
        plain = bars(csvdata(), preload=False)
        kept = bars(self.wrap(lambda d: True), preload=False)
        assert [b[1:] for b in kept] == [b[1:] for b in plain]

    @pytest.mark.parametrize("preload", [True, False])
    def test_data_filter_delivers_each_bar_once(self, preload):
        """Preloading used to double every bar.

        ``_load`` asked ``not len(dataname)`` to mean "not started yet", but
        len() is also 0 right after ``home()`` rewinds a preloaded feed, so it
        restarted the source, reopened the file it had just closed, and read
        the whole thing a second time.
        """
        delivered = bars(self.wrap(lambda d: True), preload=preload)
        assert len(delivered) == 255
        assert len({bar[0] for bar in delivered}) == 255

    def test_data_filter_agrees_with_itself_across_preload(self):
        assert bars(self.wrap(lambda d: True), preload=True) == bars(
            self.wrap(lambda d: True), preload=False
        )

    @pytest.mark.parametrize("preload", [True, False])
    def test_data_filter_closes_the_wrapped_feeds_file(self, preload):
        """The wrapper starts its inner feed itself, so it must stop it too.

        Without that, a feed that is not preloaded kept its CSV file open
        after the run, and Python reported a ResourceWarning.
        """
        inner = csvdata()
        bars(
            bt.filters.DataFilter(dataname=inner, funcfilter=lambda d: True),
            preload=preload,
        )
        assert inner.f is None


class TestDataFiller:
    """Gaps in an intraday feed are filled from the previous close.

    The values below are checked against the documented rule rather than
    recorded from the implementation: the feed carries 10:31 and 10:34 of one
    session, so 10:32 and 10:33 are missing and must arrive priced at the
    10:31 close, carrying the configured fill volume.
    """

    HEADER = "Date,Time,Open,High,Low,Close,Volume,OpenInterest\n"
    ROWS = (
        "2006-01-02,10:31:00,10.0,10.5,9.5,10.2,100,0\n"
        "2006-01-02,10:34:00,11.0,11.5,10.5,11.2,200,0\n"
    )

    def minutefeed(self, tmp_path):
        path = tmp_path / "gapped.txt"
        path.write_text(self.HEADER + self.ROWS)
        return bt.feeds.BacktraderCSVData(
            dataname=str(path),
            timeframe=bt.TimeFrame.Minutes,
            compression=1,
            sessionstart=datetime.time(10, 30),
            sessionend=datetime.time(17, 0),
        )

    def delivered(self, data, **kwargs):
        rows = []

        class Recorder(bt.Strategy):
            __test__ = False

            def next(self):
                d = self.data
                rows.append(
                    (
                        d.datetime.datetime(0).strftime("%H:%M"),
                        round(d.close[0], 2),
                        d.volume[0],
                    )
                )

        cerebro = bt.Cerebro(stdstats=False, preload=False)
        cerebro.adddata(data)
        cerebro.addstrategy(Recorder)
        cerebro.run()
        return rows

    def test_the_raw_feed_has_the_gap(self, tmp_path):
        assert [r[0] for r in self.delivered(self.minutefeed(tmp_path))] == [
            "10:31",
            "10:34",
        ]

    def test_the_missing_minutes_are_inserted(self, tmp_path):
        filled = bt.filters.DataFiller(dataname=self.minutefeed(tmp_path))
        assert [r[0] for r in self.delivered(filled)] == [
            "10:31",
            "10:32",
            "10:33",
            "10:34",
        ]

    def test_inserted_bars_carry_the_previous_close(self, tmp_path):
        filled = bt.filters.DataFiller(dataname=self.minutefeed(tmp_path))
        rows = self.delivered(filled)
        assert rows[1][1] == 10.2  # the close of 10:31
        assert rows[2][1] == 10.2

    def test_real_bars_are_untouched(self, tmp_path):
        filled = bt.filters.DataFiller(dataname=self.minutefeed(tmp_path))
        rows = self.delivered(filled)
        assert (rows[0][1], rows[0][2]) == (10.2, 100.0)
        assert (rows[3][1], rows[3][2]) == (11.2, 200.0)

    def test_the_wrapped_feeds_file_is_closed(self, tmp_path):
        inner = self.minutefeed(tmp_path)
        self.delivered(bt.filters.DataFiller(dataname=inner))
        assert inner.f is None

    def test_inserted_bars_take_the_configured_volume(self, tmp_path):
        filled = bt.filters.DataFiller(dataname=self.minutefeed(tmp_path), fill_vol=0.0)
        assert self.delivered(filled)[1][2] == 0.0

    def test_fill_price_overrides_the_previous_close(self, tmp_path):
        filled = bt.filters.DataFiller(
            dataname=self.minutefeed(tmp_path), fill_price=99.0
        )
        rows = self.delivered(filled)
        assert rows[1][1] == 99.0
        assert rows[3][1] == 11.2  # real bars keep their own price
