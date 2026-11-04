# Decisions

Things that were examined and found to be correct, deliberate, or the lesser
evil. Do not re-open these without new evidence.

*Last updated: 2026-11-03*

## Upstream is dormant, and this fork already contains all of it

*2026-08-23*

Checked on 2026-08-23, after a request to pull new upstream commits: **there
are none, and there is nothing to merge.**

`mementum/backtrader` last received a commit on **2023-04-19** (`b853d7c`,
"Version 1.9.78.123"). That is the tip of both `master` and `development`. The
three other branches are older still - `fix-compression` 2018-10-10,
`merge_memento_backtrader` 2020-07-06, `numpylines` 2017-02-19 - and upstream
never merged them. The repository is not archived; it is simply inactive.

More importantly, the fork is **content-identical** to that tip. Our history
diverged from upstream's at `8ee132c` (2018-01-25) and re-applied the same work
on parallel commits, so `git log master..upstream/master` prints 165 commits
that look missing and are not: `git diff upstream/master 2a64c42` is **empty**,
byte for byte, and `2a64c42` is an ancestor of `master`. Everything after it on
`master` is this fork's own work.

The `git log` commit count is therefore the wrong instrument here and will
mislead the next reader too. Compare trees, not commit lists:

```shell
git fetch upstream
git diff upstream/master 2a64c42     # empty == fully in sync
```

`upstream` (`https://github.com/mementum/backtrader.git`) is now a configured
remote so this check costs one command. Do not re-open the question without
first seeing that diff come back non-empty.

## Distribution `slim-backtrader`, import `backtrader`

*2026-08-23*

The PyPI name `backtrader` belongs to upstream (checked 2026-08-23: the JSON
API returns 200), and a name on PyPI is never reusable — not even after the
project owning it is deleted. The fork therefore publishes as
`slim-backtrader`, which was free on the same date.

The **import** package deliberately stays `backtrader`, so `import backtrader
as bt` keeps working and no strategy code has to move. The accepted cost: this
fork and upstream cannot be installed into the same environment, because both
own the top-level `backtrader` module. Renaming the import package would
remove that clash and was rejected — it is a far larger API break than a
packaging change should carry, and it would break every consumer for the
benefit of a side-by-side install nobody has asked for.

Do not "fix" the clash by renaming the import package without that request
arriving first. See `reports/sessions/2026-08-23_pypi-packaging.md`.

## Removing the live-trading integrations

*2026-08-22*

Interactive Brokers, VisualChart and Oanda were removed wholesale, along with
the blaze, InfluxDB and Quandl feeds and the pyfolio analyzer. The decision was
made on dependency evidence, not on taste — each one requires a package that
cannot be installed or used on Python 3.13:

| removed | required | state |
|---|---|---|
| IB store/broker/feed | `ib.opt`, `ib.ext` (IbPy) | Python 2 only, unmaintained |
| VisualChart store/broker/feed | `comtypes`, `_winreg` | `_winreg` is the Python 2 spelling; the product is retired; Windows only |
| Oanda store/broker/feed | `oandapy` | unmaintained; REST v1 discontinued by Oanda |
| blaze feed | `blaze` | no release since 2016 |
| InfluxDB feed | `influxdb` 1.x client | the 1.x server line is end-of-life |
| Quandl feed | quandl.com HTTP API | retired into Nasdaq Data Link |
| pyfolio analyzer | `pyfolio` | abandoned; already marked deprecated upstream |

They had been imported under `try: ... except ImportError: pass`, so they were
silently absent for years rather than failing loudly. That pattern is why the
rot went unnoticed, and it is not reintroduced: what remains either has no
dependency at all or imports it lazily with a clear error message.

The VisualChart *file* readers (`vchart`, `vchartcsv`) went with the rest of
the family even though they had no dependency — they read files produced by a
product that no longer ships.

## Keeping the CSV feeds that have no dependencies

*2026-08-22*

`SierraChartCSVData` and `MT4CSVData` are four-line subclasses of
`GenericCSVData`. They cost nothing, work offline and cannot rot, so "slim
down" does not apply to them.

## Keeping the TA-Lib bindings

*2026-08-22*

`backtrader/talib.py` is 3% covered and imports `talib`, but TA-Lib is alive and
maintained, and the import is lazy. It stays, behind the `talib` extra.

## Plotting shows figures where the backend can

*2026-08-22, reversed 2026-10-29*

From commit `ea3d0d3` until 2026-10-29, `plotter.show()` was commented out and
the backend forced to `Agg` (`MacOSX` on darwin). That made the suite able to
render headless, but it left no way to see a chart without saving it by hand.
On 2026-10-29 the owner asked for a modern pyplot setup instead. Now:

- matplotlib chooses the backend (`MPLBACKEND`, `matplotlibrc`, detection;
  `Agg` when there is no display), and `cerebro.plot(use=...)` overrides it.
- `cerebro.plot()` calls `pyplot.show()` unless the backend is file-only.
  That is never a hang on a headless machine and never matplotlib's
  "non-interactive" warning.
- The suite stays headless through `MPLBACKEND=Agg` in `tests/conftest.py`,
  not through the library. Do not move that pin back into `backtrader/plot/`:
  forcing a backend at import time is what broke notebooks and windows alike.

## AnnualReturn's dependency on the Broker observer

*2026-08-22*

`AnnualReturn` reads `strategy.stats.broker` and therefore raises
`AttributeError` under `stdstats=False`. Its own source says "Must have
stats.broker". Left as it is — changing it would alter the analyzer's contract
— but now pinned by a test so the coupling is visible rather than surprising.

## `todate` excludes a daily bar stamped at the session end

*2026-08-22*

A daily bar carries `23:59:59.999` as its time, so `todate=datetime(2006, 6, 30)`
excludes 2006-06-30. This looks like an off-by-one when splitting a feed on a
date boundary; it is the documented consequence of session-end stamping.
Pinned by `test_todate_excludes_a_bar_stamped_at_the_session_end`.

## A closing order's `executed.value` is the cost of what it closed

*2026-11-03*

A sell that closes a long reports `executed.value` equal to the position's
*cost*, not the sale's proceeds: `SELL -8728 @ 11.41`, value 91,361.01, the
same as the buy. Upstream does this deliberately: `value` is the capital the
order opened or released, and `Trade.pnl` carries the difference. Use
`abs(executed.size) * executed.price` for what changed hands. Found while
logging trades in the AAPL/MSFT notebook.

## In `next_open()`, indicators still show the bar that just closed

*2026-11-03*

With `cheat_on_open=True`, `next_open()` runs after the new bar's open is
loaded and before the broker fills. Data lines already show the new bar;
indicators have not moved, so `cross[0]` is the crossover of the bar that
just closed. Using `cross[-1]` there (as if the indicators had moved) trades
a day late. Checked on 2026-11-03 to give the same fills with `runonce`,
`runonce=False` and `preload=False`; upstream's cheat-on-open sample reads
`[0]` the same way.

## `add_cash` reaches the account on the broker's next cycle

*2026-11-03*

`broker.add_cash()` queues the amount; it is added when the broker next
runs, so an `order_target_*` sent on the same bar still sizes on the old
value. Invest a deposit on the following bar. In fund mode the deposit
buys shares at the share value of the bar it lands on, which is what makes
the fund's return ignore it (checked 2026-11-03: share value 114.83 before
a 50,000 deposit, 114.77 after it).

## How CI and publishing are wired, and what was rejected

*2026-08-24*

`.github/workflows/ci.yml` gates changes; `.github/workflows/release.yml`
publishes on a `vX.Y.Z` tag. The choices behind them, so they are not re-argued:

- **Trusted publishing (OIDC), not an API token.** PyPI is configured to trust
  this workflow file, in this repository, in the `pypi` environment, and mints
  a credential valid for one upload. The alternative was a repository secret,
  which is a standing credential that leaks by being copied — and the token
  that uploaded 2.0.0–2.1.0 was already pasted into a chat transcript once. The
  narrower consequence matters too: a token in `secrets` is usable by any
  workflow in the repository, an OIDC trust is usable by one.
- **Actions pinned to a commit SHA, with the version in a trailing comment.**
  A tag is mutable, and one of these actions is handed a credential that can
  publish. Refresh a pin with
  `git ls-remote --tags https://github.com/<owner>/<repo>`.
- **No Dependabot.** It would keep those pins fresh and it is the obvious
  companion to them — but it works by opening pull requests, and this
  repository has no PR workflow. Refreshing pins by hand at release time is the
  smaller cost. Reconsider if the repository ever takes contributions.
- **No Codecov or any third-party analytics.** Coverage is measured in CI,
  enforced with `--cov-fail-under`, and kept as a build artefact. Sending the
  repository's coverage to an external service to get a badge would add an
  account, a token and a network dependency for something a job summary already
  prints.
- **Publishing is a tag push, not a "Publish release" click.** The tag is what
  a maintainer already creates, and it is scriptable. The version guard makes
  the failure mode — tagging `v2.2.0` against `__version__ = "2.1.0"` — a red
  build instead of an unusable upload, which matters because PyPI never lets a
  version be uploaded twice.
- **The release workflow verifies the artefact, not the working tree.** Its
  `verify` job deliberately does not check out the repository: it installs the
  sdist and runs the suite the sdist itself ships. Testing the checkout would
  have re-tested what CI already tested and would have missed exactly the
  defect that shipped in 2.0.0.
