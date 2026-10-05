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
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import json
from email.message import Message
from unittest import mock
from urllib.request import HTTPRedirectHandler

import testcommon  # noqa: F401

import backtrader.feeds as btfeeds


def _start(payload, apikey=None):
    captured = []

    def fake_urlopen(request):
        captured.append(request)
        return io.BytesIO(json.dumps(payload).encode('utf-8'))

    data = btfeeds.FXMacroData(dataname='EURUSD', apikey=apikey)
    with mock.patch('backtrader.feeds.fxmacrodata.urlopen', fake_urlopen):
        data.start()
    return data, captured


def test_apikey_not_forwarded_on_redirect():
    data, captured = _start({'detail': 'Not found'}, apikey='test-key')
    request = captured[0]
    redirected = HTTPRedirectHandler().redirect_request(
        request, None, 302, 'Found', Message(), 'https://elsewhere.test/')
    assert request.get_header('X-api-key') == 'test-key'
    assert redirected.get_header('X-api-key') is None


def test_invalid_apikey_not_echoed_in_error():
    data, captured = _start({'data': []}, apikey='test-key\r\nX-Other: 1')
    assert not captured
    assert 'test-key' not in data.error


def test_error_body_sets_clean_error():
    data, _ = _start({'detail': 'Not found'})
    assert data.error == 'Unexpected FXMacroData response: Not found'

    data, _ = _start(['unexpected'])
    assert data.error == 'Unexpected FXMacroData response: no data list'


if __name__ == '__main__':
    test_apikey_not_forwarded_on_redirect()
    test_invalid_apikey_not_echoed_in_error()
    test_error_body_sets_clean_error()
