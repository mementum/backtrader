# Testing suite

What is tested, how it is selected, and what it costs.

*Last updated: 2026-11-03*

## Running it

```shell
conda activate backtrader
pytest                  # 698 tests, ~80 s (2026-11-03)
pytest --cov            # adds coverage, ~4 min
pytest -m "not plotting"   # skip the 13 matplotlib rendering tests
```

`pytest` is configured in `pyproject.toml`: `testpaths = ["tests"]`, so it runs
from the repository root. The suite is offline, needs no credentials and must
stay that way. `filterwarnings` turns backtrader's own `DeprecationWarning`s
and any `SyntaxWarning` into errors.

## Where it runs

Locally first — `pytest` in the conda env is the fast answer — and then on
GitHub Actions, since 2026-08-24. `.github/workflows/ci.yml` is the gate on
every push to any branch, every pull request, and on demand. Every branch and
not only `master`, because feature work here merges locally rather than through
a pull request: on `master` alone, CI would run after the merge it was meant to
gate.

| job | what it establishes | duration |
|---|---|---|
| `black` | the tree is formatted; Black is pinned exactly, because its stable style changes between releases | 13-18 s |
| `pytest` 3.13, Linux | the suite, with the optional extras installed | 67-91 s |
| `pytest` 3.14, Linux | the same on the newer interpreter | 93 s |
| `pytest` 3.13, macOS | that `OS Independent` holds | 69-71 s |
| `pytest` 3.13, Windows | the same, and the slowest row of the four | 126-134 s |
| `coverage` | `--cov-fail-under=70`, a backstop against collapse rather than a target | 207-277 s |
| `build and verify artefacts` | see below | 75-76 s |
| `CI passed` | the aggregate the other seven report into | 3-4 s |

**Wall clock 3 min 33 s and 4 min 45 s; 661 s and 756 s of job time.** Measured
2026-08-24 over runs #1 and #2 - the branch push and the merge to `master`, the
first two runs there have ever been - by reading `started_at` and `completed_at`
from `/repos/dennisdeh/backtrader-slim/actions/runs/<id>/jobs`. Two samples, so
these are a range and not a benchmark; the spread on `coverage` and on Linux
3.13 is runner variance, not anything in the suite.

The jobs run in parallel, so wall clock is `coverage` plus scheduling: it is the
long pole by roughly a factor of two over the next job, and the only one worth
moving if the gate ever needs to be faster. Windows costs about twice what Linux
and macOS do for the same 434 tests.

`CI passed` aggregates the rest, so branch protection needs one rule and a new
job needs no edit to it.

Four things about the matrix are deliberate:

- **`fail-fast: false`.** A red platform must not hide the state of the others.
- **The Linux 3.13 row installs `[dev,calendars]`.** Without
  `pandas_market_calendars` the trading-calendar test skips itself and says so
  to nobody. One row carrying the optional extras is what exercises those paths.
- **macOS and Windows are gates, not decoration.** `pyproject.toml` claims
  `Operating System :: OS Independent`. Before those rows existed the claim had
  never been executed anywhere. What made them plausible enough to make
  blocking, checked on 2026-08-24: the package imports nothing POSIX-only, its
  only `sys.platform` branches are the plotting backend (guarded by
  `except Exception`) and a win32 branch in `utils/flushfile.py`, `datas/` is
  pure ASCII so a locale-default `open()` cannot mis-decode it, and the
  optimization tests pass under the `spawn` start method — verified by forcing
  `multiprocessing.set_start_method("spawn")`, which is what macOS and Windows
  use and Linux does not.
- **A macOS job that gets no runner does not block; one that fails does.**
  On 2026-10-29, from about 14:45 UTC, GitHub gave this repository no hosted
  macOS runner: six jobs in a row, on `macos-latest` and on a pinned
  `macos-15`, sat queued and were cancelled after exactly 15 minutes, with no
  log and no reason recorded (runs #33 and #35, each re-run once, #37, and
  #38 on `macos-15`).
  The repository is public, so it was not billing, and the workflow sets no
  timeout. Every other job was green, but `CI passed` needed all of them, so
  nothing could reach `master`. macOS is now its own job, `test-macos`, and
  `CI passed` accepts it as `abandoned`, with a warning, while still failing
  on `failure` or `cancelled`. `abandoned` is what `needs` reports for a job
  never given a runner, though the API and the web page call it `cancelled`;
  the first version of this check accepted `cancelled` and failed on that
  (run #39). The cost: a commit can reach `master` without a macOS run,
  and every run waits 15 minutes for one while runners are missing. Run #40
  (2026-10-29) was given a macOS runner again; keeping the exemption is a
  choice to revisit, not a necessity.

## What the artefact job checks that the suite cannot

`pytest` in a clone says nothing about what gets uploaded. 2.0.0 shipped an
sdist whose tests could not run at all — setuptools' legacy heuristic matched
`tests/test*.py` and left out `conftest.py` and `datas/`, so all 88 test
modules failed at collection. The suite was green throughout.

So the job builds both artefacts and then:

- asserts the sdist contains `conftest.py`, `testcommon.py`, a data file and
  the licence — named files, so the failure says which one is missing;
- asserts neither artefact carries `.pyc` or `__pycache__`;
- installs the **sdist** into an empty venv with pytest and pyflakes and
  nothing else, and runs the suite the sdist ships. **426 passed, 9 skipped**
  (2026-08-24) — the nine are the optional-package tests, and that they skip
  rather than fail is the property being checked;
- installs the **wheel** into an empty venv, asserts `pip freeze` lists exactly
  one package, and runs `import backtrader` and `btrun --help` from outside the
  source tree.

That third check found a real defect on 2026-08-24:
`test_numpy_arrives_only_when_hurst_is_built` asserts numpy *arrives* when
`HurstExponent` is built, and so needs numpy present — but had no
`importorskip`, so it failed rather than skipped for anyone running the suite
without the optional packages. The convention its neighbours already followed
is now in CLAUDE.md.

## What is in it

| file | tests | subject |
|---|---|---|
| `test_ind_*.py` (70 files) | 70 | golden-value regressions, one per indicator |
| `test_analyzers.py` | 34 | every built-in analyzer |
| `test_cerebro.py` | 34 | running, optimisation, resampling, timers, writer, observer buffers, plotting, the btrun CLI |
| `test_options_pricing.py` | 30 | pricing against Hull's worked examples, parity, tree convergence, greeks by finite differences, implied volatility |
| `test_options_settlement.py` | 30 | option positions through cerebro: valuation, commission, cash and physical settlement, assignment, intraday expiry |
| `test_options_chain.py` | 18 | chain sources (pandas, CSV, partitioned, model), views' bars and gaps, settlement, selection by moneyness and delta, all run modes, margin and quote fills on views; skipped without numpy |
| `test_options_attribution.py` | 4 | the greek split adds up to the whole gain, theta on a flat market, a stock is all delta, delta on a trend |
| `test_options_fills.py` | 14 | quote fills: mid +/- a fraction of the spread, by side, cheat-on-close, close orders, combos, missing quotes |
| `test_options_combos.py` | 20 | the `CashCovered` rules, margin at submission and after a bar, combo orders filling whole or not at all, `PortfolioGreeks`, `StructureTrades` |
| `test_options_model.py` | 25 | `ModelOptionData` against prices and realised volatility recomputed from the CSV, listing, moneyness, all run modes, settlement |
| `test_ind_optiongreeks.py` | 18 | `OptionGreeks` in all twelve run modes against a fixture priced at 20% volatility, and the fixture against its generator |
| `test_examples.py` | 52 | every script in `examples/` runs and prints something, and plots; skips one whose `REQUIRES` package is missing; the notebook's code compiles (it needs Yahoo Finance, so it is not run) |
| `test_plot.py` | 10 | the date axis (labels, tick placement, timezone, weekend gaps), when figures are shown, `use=`, fresh figures |
| `test_utils.py` | 27 | date conversion, AutoDict family, mathsupport, TimeFrame |
| `test_orders_advanced.py` | 19 | stop/trailing/bracket/OCO orders, order_target_* |
| `test_broker.py` | 20 | cash and value accounting, order types, commission, slippage |
| `test_resampling_intraday.py` | 18 | intraday resample/replay, trading calendar, PSAR, PivotPoint |
| `test_feeds.py` | 20 | CSV family, PandasData, Chainer, RollOver |
| `test_filters_sizers.py` | 57 | filters, sizers, fillers, commission schemes, bar splitters, data wrappers |
| `test_strategy_*.py`, `test_writer.py`, others | 10 | strategy runs, writer output |
| `test_metaclass.py` | 6 | the `frompackages` directive, that nothing optional is imported eagerly, and that pyflakes finds no undefined name |
| `test_licensing.py` | 5 | GPLv3 notices, upstream copyright, modification notices, LICENSE, README attribution |
| `test_concurrency.py` | 21 | the optimization executors, `ObjectCache`, concurrent cerebros |
| `test_position.py` | 26 | size/price arithmetic, every branch of `set` and `update` |
| `test_trade.py` | 21 | the trade lifecycle, both directions, `TradeHistory` |
| `test_chaos.py` | 87 | malformed input, raising callbacks, nonsense orders, `Store` |

## The golden-value contract

The indicator tests are regressions against recorded output. `chkvals` holds
the indicator's value formatted to six decimals at three points — the latest
bar, the first valid bar, and the midpoint — plus `chkmin`, the computed
minimum period.

`testcommon.runtest` runs each case across every combination of
`runonce ∈ {True, False}`, `preload ∈ {True, False}` and
`exactbars ∈ {-2, -1, False}`. An indicator has two independent
implementations — `next()` bar by bar and `once()` vectorised — and this matrix
is what stops a fix landing in only one of them.

**A changed golden value means the library computes something different.**
Never edit one to make a test pass: either the change was intended, and it is
recorded in `changelog.txt`, or it is a bug.

Regenerate a block by running the test file directly
(`python tests/test_ind_sma.py`), which prints it via `main=True` — but that
generator blesses whatever the implementation currently does, so check the
numbers against the formula before pasting them in.

## Fixtures

`tests/conftest.py` holds the shared paths and fixtures. Data comes from
`datas/`, which is tracked, so a fresh clone can run the suite immediately.
`csvdata()` builds the standard 2006 daily feed; `daily_data`, `weekly_data`,
`cerebro` and `cerebro_with_data` are the fixtures. It also sets
`MPLBACKEND=Agg` before anything imports matplotlib. `cerebro.plot()` shows
figures on any GUI backend, so without the pin a developer's machine, or a
macOS or Windows CI runner, would open windows and block the run.

The `bt.Strategy` subclasses used inside tests are named `TestStrategy` for
historical reasons and carry `__test__ = False`, because pytest would otherwise
try to collect them as test classes.

## Coverage

**76% of statements**, 72% once branches are counted (10618 statements, 3318
branches, measured 2026-08-23). It was 73%/69% on 2026-08-22, and **43%**
statement-only over 14205 statements before the slimming session — the
statement count fell because the dead integrations were deleted.

`reports/IMPROVEMENT_SUGGESTIONS.md` lists which modules are still thin and
which of them cannot be covered offline.

Markers: `plotting` (needs matplotlib) and `network` (needs internet; nothing
currently uses it, and nothing should without being marked).

## Known defects are pinned, not skipped

**There are no `xfail`s in the suite as of 2026-08-23** — every defect they
guarded has been fixed. The convention stands for the next one.

A defect that cannot be fixed immediately gets a test either way:

- reproducible — `@pytest.mark.xfail(..., strict=True)`. `strict` matters: the
  day someone fixes it, the test reports an *unexpected pass* and fails the
  run, so the fix cannot land without the entry moving out of `OPEN_ITEMS.md`.
  A plain `xfail` would quietly go green and leave the record stale.
- inert, or a deliberate-looking oddity — a test that asserts today's
  behaviour, with a docstring saying it is pinned rather than endorsed.

Both of those happened this session, and both then turned into ordinary
passing tests when the defects were fixed. That is the point: never leave a
known defect unpinned, and never let a pinned one be mistaken for intended
behaviour.

## Chaos: breaking things on purpose

`test_chaos.py` asks what happens when the inputs are wrong, and holds two
rules apart.

**Nothing a user writes may be swallowed.** A strategy, indicator, analyzer,
observer, sizer or writer that raises has found something the caller needs to
see; a run that quietly finishes after eating the exception has computed the
wrong answer and said nothing. Every such callback is covered, in both
execution paths, and `KeyboardInterrupt`, `SystemExit` and `MemoryError` are
covered too — those are what a bare `except:` takes with it.
`StrategySkipError` is the single deliberate exception, and is tested as one.

**Broken input must be reported precisely.** A malformed row names the file,
the line and the row, and raises `ValueError` — never a bare `StopIteration`,
and never a silently fabricated value.

Two of the tests are mechanical rather than behavioural: the package must
contain no bare `except:` and must never catch `BaseException`. Both defects
this pair guards against were real, and CLAUDE.md prefers a check that can be
run to a rule that has to be remembered.

Where a finding is real but fixing it is a behaviour decision — bars are never
checked for time order, a negative-size buy is refused as a margin failure —
the test asserts today's behaviour and `OPEN_ITEMS.md` carries the reasoning.

## Measuring, rather than testing

`python tools/benchmark.py` reports where the engine spends its time: engine
phases, per-indicator cost in both execution modes, a cProfile of the hot path,
and import cost. It is offline and deterministic, reading only `datas/`.

It is not part of the suite and nothing asserts on its numbers — a timing
threshold on a shared machine is a flaky test. It exists so that a performance
claim can carry the number and the command that produced it, which
`CLAUDE.md` requires. Current figures are in
`reports/IMPROVEMENT_SUGGESTIONS.md`, dated.
