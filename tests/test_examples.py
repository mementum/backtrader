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
"""Every script in examples/ runs, and says something.

The examples are documentation that executes. Each is run here through its
``main()``, so one that an API change breaks fails the suite instead of
misleading its next reader. An example names the optional packages it needs
in ``REQUIRES``; it is skipped where they are missing.
"""

import ast
import importlib.util
import inspect
import sys
from pathlib import Path

import pytest

EXAMPLES = sorted(
    (Path(__file__).resolve().parent.parent / "examples").glob("[0-9][0-9]_*.py")
)


def _requires(path):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "REQUIRES":
            return ast.literal_eval(node.value)
    raise AssertionError(f"{path.name} does not declare REQUIRES")


def _param(path):
    marks = [pytest.mark.plotting] if "matplotlib" in _requires(path) else []
    return pytest.param(path, id=path.stem, marks=marks)


def test_the_examples_are_there():
    assert len(EXAMPLES) >= 25


@pytest.mark.parametrize("path", [_param(p) for p in EXAMPLES])
def test_example_runs(path, capsys, tmp_path, monkeypatch):
    for package in _requires(path):
        if importlib.util.find_spec(package) is None:
            pytest.skip(f"{path.name} needs {package}")
    # a real module in sys.modules, as `python example.py` would have:
    # backtrader's metaclasses look a class's module up there
    name = f"example_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    if "out" in inspect.signature(module.main).parameters:
        module.main(out=tmp_path / "chart.png")
    else:
        module.main()
    assert capsys.readouterr().out.strip()


@pytest.mark.plotting
@pytest.mark.parametrize("path", [_param(p) for p in EXAMPLES])
def test_example_plots(path, tmp_path, monkeypatch):
    if importlib.util.find_spec("matplotlib") is None:
        pytest.skip("plotting requires matplotlib")
    for package in _requires(path):
        if importlib.util.find_spec(package) is None:
            pytest.skip(f"{path.name} needs {package}")
    name = f"example_{path.stem}_plot"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    sig = inspect.signature(module.main).parameters
    if "plot" in sig:
        module.main(plot=True)
    elif "out" in sig:
        module.main(out=tmp_path / "chart_plot.png")
