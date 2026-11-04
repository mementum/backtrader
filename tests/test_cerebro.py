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
"""Cerebro's public surface: configuration, running, optimisation, observers,
writers, timers and plotting.

cerebro.py, plot/ and btrun/ carried 0-60% coverage and no direct tests.
"""

import datetime
import io

import pytest

import backtrader as bt

from conftest import csvdata, datafile


class Noop(bt.Strategy):
    __test__ = False

    params = dict(period=10)

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data, period=self.p.period)
        self.ran = 0

    def next(self):
        self.ran += 1


class TestRunning:
    def test_run_returns_one_instance_per_strategy(self, cerebro_with_data):
        cerebro_with_data.addstrategy(Noop)
        strats = cerebro_with_data.run()
        assert len(strats) == 1
        assert isinstance(strats[0], Noop)

    def test_two_strategies_both_run(self, cerebro_with_data):
        cerebro_with_data.addstrategy(Noop)
        cerebro_with_data.addstrategy(Noop, period=20)
        strats = cerebro_with_data.run()
        assert len(strats) == 2
        assert strats[0].p.period == 10
        assert strats[1].p.period == 20

    def test_strategy_params_reach_the_instance(self, cerebro_with_data):
        cerebro_with_data.addstrategy(Noop, period=33)
        assert cerebro_with_data.run()[0].p.period == 33

    def test_next_is_called_once_per_bar_after_minperiod(self, cerebro_with_data):
        cerebro_with_data.addstrategy(Noop, period=10)
        strat = cerebro_with_data.run()[0]
        assert strat.ran == 255 - 10 + 1

    def test_runonce_and_next_agree(self, daily_data):
        results = {}
        for runonce in (True, False):
            cerebro = bt.Cerebro(stdstats=False, runonce=runonce)
            cerebro.adddata(csvdata())
            cerebro.addstrategy(Noop)
            results[runonce] = cerebro.run()[0].sma[0]
        assert results[True] == pytest.approx(results[False])

    def test_preload_off_produces_the_same_result(self):
        results = {}
        for preload in (True, False):
            cerebro = bt.Cerebro(stdstats=False, preload=preload, runonce=False)
            cerebro.adddata(csvdata())
            cerebro.addstrategy(Noop)
            results[preload] = cerebro.run()[0].sma[0]
        assert results[True] == pytest.approx(results[False])

    def test_exactbars_limits_memory_but_keeps_the_last_value(self):
        cerebro = bt.Cerebro(stdstats=False, exactbars=1, runonce=False)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Noop)
        strat = cerebro.run()[0]
        assert strat.sma[0] > 0


class TestOptimisation:
    def test_optstrategy_runs_every_combination(self):
        cerebro = bt.Cerebro(stdstats=False, maxcpus=1)
        cerebro.adddata(csvdata())
        cerebro.optstrategy(Noop, period=range(10, 15))
        results = cerebro.run()
        assert len(results) == 5

    def test_optreturn_gives_back_params_only(self):
        cerebro = bt.Cerebro(stdstats=False, maxcpus=1, optreturn=True)
        cerebro.adddata(csvdata())
        cerebro.optstrategy(Noop, period=[10, 20])
        results = cerebro.run()
        assert [r[0].p.period for r in results] == [10, 20]

    def test_optcallback_is_invoked(self):
        seen = []
        cerebro = bt.Cerebro(stdstats=False, maxcpus=1)
        cerebro.adddata(csvdata())
        cerebro.optstrategy(Noop, period=[10, 20])
        cerebro.optcallback(lambda cb: seen.append(cb))
        cerebro.run()
        assert len(seen) == 2


class TestBrokerConfiguration:
    def test_setcash_before_run_is_the_starting_value(self, cerebro_with_data):
        cerebro_with_data.broker.setcash(5000.0)
        cerebro_with_data.addstrategy(Noop)
        cerebro_with_data.run()
        assert cerebro_with_data.broker.startingcash == 5000.0

    def test_broker_can_be_replaced(self, cerebro_with_data):
        broker = bt.brokers.BackBroker(cash=777.0)
        cerebro_with_data.setbroker(broker)
        assert cerebro_with_data.getbroker() is broker

    def test_add_observer_shows_up_in_stats(self, cerebro_with_data):
        cerebro_with_data.addobserver(bt.observers.Broker)
        cerebro_with_data.addstrategy(Noop)
        strat = cerebro_with_data.run()[0]
        assert len(strat.stats) >= 1


class TestResampling:
    def test_resampledata_to_weekly_reduces_the_bar_count(self):
        bars = []

        class Counter(bt.Strategy):
            __test__ = False

            def next(self):
                bars.append(self.data.datetime.date(0))

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.resampledata(csvdata(), timeframe=bt.TimeFrame.Weeks)
        cerebro.addstrategy(Counter)
        cerebro.run()
        assert 50 <= len(bars) <= 53

    def test_resampledata_to_monthly(self):
        bars = []

        class Counter(bt.Strategy):
            __test__ = False

            def next(self):
                bars.append(self.data.datetime.date(0))

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.resampledata(csvdata(), timeframe=bt.TimeFrame.Months)
        cerebro.addstrategy(Counter)
        cerebro.run()
        assert len(bars) == 12

    def test_replaydata_keeps_the_original_bar_count(self):
        bars = []

        class Counter(bt.Strategy):
            __test__ = False

            def next(self):
                bars.append(len(self))

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.replaydata(csvdata(), timeframe=bt.TimeFrame.Weeks)
        cerebro.addstrategy(Counter)
        cerebro.run()
        assert len(bars) == 255  # every daily bar replays into its week


class TestTimers:
    def test_timer_fires_on_the_requested_schedule(self):
        fired = []

        class Timed(bt.Strategy):
            __test__ = False

            def __init__(self):
                self.add_timer(when=bt.timer.SESSION_START)

            def notify_timer(self, timer, when, *args, **kwargs):
                fired.append(when)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Timed)
        cerebro.run()
        assert len(fired) == 255

    def test_monthly_timer_fires_once_per_month(self):
        fired = []

        class Timed(bt.Strategy):
            __test__ = False

            def __init__(self):
                self.add_timer(
                    when=bt.timer.SESSION_START, monthdays=[1], monthcarry=True
                )

            def notify_timer(self, timer, when, *args, **kwargs):
                fired.append(when)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Timed)
        cerebro.run()
        assert len(fired) == 12


class TestWriter:
    def test_writer_emits_a_csv_report(self):
        out = io.StringIO()
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Noop)
        cerebro.addwriter(bt.WriterFile, out=out, csv=True)
        cerebro.run()
        text = out.getvalue()
        assert "Cerebro" in text
        assert len(text.splitlines()) > 100


class TestObserverBuffers:
    """In run-once mode an observer's buffer was sized for the run and then
    grown again bar by bar: twice the memory, and a tail of NaN after the
    last bar for anything reading ``.array``."""

    @staticmethod
    def value_line(runonce, *names):
        cerebro = bt.Cerebro(stdstats=False, runonce=runonce)
        for name in names:
            cerebro.adddata(csvdata(name))
        cerebro.addobserver(bt.observers.Value)
        cerebro.addstrategy(Noop)
        strat = cerebro.run()[0]
        return len(strat), list(strat.getobservers()[0].lines.value.array)

    @pytest.mark.parametrize(
        "names",
        [
            ("2006-day-001.txt",),
            # the weekly feed is the clock, so the run has more bars than
            # the buffer sized from it
            ("2006-week-001.txt", "2006-day-001.txt"),
        ],
        ids=["one feed", "more bars than the clock's buffer"],
    )
    def test_an_observer_holds_one_value_per_bar(self, names):
        bars, once = self.value_line(True, *names)
        assert len(once) == bars
        assert once == self.value_line(False, *names)[1]


class TestWriterDates:
    def test_the_strategy_writes_its_datetime_as_a_date(self):
        """The data feed's column was a date, the strategy's beside it the
        raw date number (734870.99...)."""
        import csv
        import io

        out = io.StringIO()
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Noop)
        cerebro.addwriter(bt.WriterFile, out=out, csv=True)
        cerebro.run()
        rows = [r for r in csv.reader(io.StringIO(out.getvalue())) if r]
        header = next(r for r in rows if r[0] == "Id")
        first = next(r for r in rows if r[0] == "1")
        dates = [first[i] for i, h in enumerate(header) if h == "datetime"]
        assert len(dates) == 2  # the data's and the strategy's
        assert dates[0] == dates[1]
        assert dates[0].startswith("2006-01-02")


class TestPlotting:
    @pytest.mark.plotting
    def test_plot_renders_without_a_display(self):
        """plot/ is ~1000 statements that nothing exercised. conftest pins the
        Agg backend, so this renders a figure and never opens a window."""
        pytest.importorskip("matplotlib")
        cerebro = bt.Cerebro(stdstats=True)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Noop)
        cerebro.run()
        figs = cerebro.plot(iplot=False)
        assert figs
        assert figs[0]

    @pytest.mark.plotting
    def test_plot_with_observers_and_analyzers(self):
        pytest.importorskip("matplotlib")
        cerebro = bt.Cerebro(stdstats=True)
        cerebro.adddata(csvdata())
        cerebro.addstrategy(Noop)
        cerebro.addobserver(bt.observers.DrawDown)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio)
        cerebro.run()
        assert cerebro.plot(iplot=False, volume=False)


class TestBtrunCLI:
    def test_btrun_runs_a_backtest_from_the_command_line(self, capsys):
        from backtrader.btrun import btrun

        btrun(
            [
                "--data",
                datafile("2006-day-001.txt"),
                "--format",
                "btcsv",
                "--strategy",
                ":SMA_CrossOver",
                "--nostdstats",
            ]
        )
        # it ran to completion without raising; that is the contract
        assert True

    def test_btrun_rejects_an_unknown_format(self):
        from backtrader.btrun import btrun

        with pytest.raises(SystemExit):
            btrun(["--data", datafile("2006-day-001.txt"), "--format", "nope"])


class TestMemorySavingWithFeedsEndingEarly:
    """exactbars=1 keeps a data line as short as its minimum period. Making
    room for the next bar used to push the current one out before knowing
    whether a next bar would come; at a feed's end nothing was left, and the
    broker's valuation read an empty buffer (IndexError)."""

    def _run(self, exactbars, close_on=3):
        from test_options_settlement import DAYS, UND_UP, underlying

        class Trade(bt.Strategy):
            def next(self):
                if len(self) == 1:
                    self.buy(data=self.datas[1], size=1)
                if close_on and len(self) == close_on:
                    self.close(data=self.datas[1])

        cerebro = bt.Cerebro(stdstats=False, exactbars=exactbars)
        cerebro.adddata(underlying(UND_UP), name="long")
        cerebro.adddata(underlying(UND_UP[:5], DAYS[:5]), name="short")  # ends early
        cerebro.addstrategy(Trade)
        cerebro.run()
        return cerebro.broker.getvalue()

    def test_a_closed_position_on_an_ended_feed(self):
        assert self._run(exactbars=1) == self._run(exactbars=False)

    def test_an_open_position_stays_valued_at_its_last_close(self):
        # bought at bar 2's open (101); the feed's last close is 105: +4
        assert self._run(exactbars=1, close_on=None) == 10000.0 + 4.0
        assert self._run(exactbars=False, close_on=None) == 10000.0 + 4.0


class _Record(bt.Strategy):
    def __init__(self):
        self.inds = [bt.ind.SMA(period=10), bt.ind.EMA(period=8), bt.ind.RSI(period=6)]
        self.rows = []

    def next(self):
        self.rows.append(
            tuple(round(i[0], 9) for i in self.inds)
            + tuple((d.datetime[0], d.open[0], d.close[0]) for d in self.datas)
        )


MEMORY_CASES = {
    "single": lambda c: c.adddata(csvdata()),
    "aligned": lambda c: (c.adddata(csvdata()), c.adddata(csvdata())),
    # 2006-day-002 trades about every other day
    "unaligned": lambda c: (
        c.adddata(csvdata()),
        c.adddata(csvdata("2006-day-002.txt")),
    ),
    "unaligned, sparse first": lambda c: (
        c.adddata(csvdata("2006-day-002.txt")),
        c.adddata(csvdata()),
    ),
    "resampled weekly": lambda c: (
        c.adddata(csvdata()),
        c.resampledata(csvdata(), timeframe=bt.TimeFrame.Weeks),
    ),
    "replayed weekly": lambda c: c.replaydata(csvdata(), timeframe=bt.TimeFrame.Weeks),
}


@pytest.mark.parametrize("case", list(MEMORY_CASES))
def test_exactbars_1_sees_what_unbounded_buffers_see(case):
    # Every bar's indicators and every feed's current bar, compared with
    # the unbounded run. Before 2026-10-29 the unaligned cases raised and the
    # resampled one silently differed from 2006-01-16 on: a rewound bar was
    # loaded past instead of delivered, because a QBuffer is always "short"
    rows = {}
    for exactbars in (False, 1):
        cerebro = bt.Cerebro(stdstats=False, exactbars=exactbars)
        MEMORY_CASES[case](cerebro)
        cerebro.addstrategy(_Record)
        rows[exactbars] = cerebro.run()[0].rows
    assert rows[1] == rows[False]
