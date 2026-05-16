#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import testcommon

from backtrader.btrun.btrun import parse_kwargs


def test_parse_kwargs_literals():
    kwargs = parse_kwargs(
        "preload=True, maxcpus=2, name='sample', values=[1, 2]")

    assert kwargs == dict(preload=True,
                          maxcpus=2,
                          name='sample',
                          values=[1, 2])


def test_parse_kwargs_empty():
    assert parse_kwargs('') == dict()


def test_parse_kwargs_rejects_code_execution():
    try:
        parse_kwargs("x=__import__('os').system('echo vulnerable')")
    except ValueError:
        pass
    else:
        raise AssertionError('parse_kwargs should reject function calls')


if __name__ == '__main__':
    test_parse_kwargs_literals()
    test_parse_kwargs_empty()
    test_parse_kwargs_rejects_code_execution()
