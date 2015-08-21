#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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

import six

import pandas as pd

from backtrader import date2num
import backtrader.feed as feed


class PandasData(feed.DataBase):
    '''
    The ``dataname`` parameter inherited from ``feed.DataBase``  is the pandas
    Time Series
    '''

    params = (
        # Possible values for datetime (must always be present)
        #  None : datetime is the "index" in the Pandas Dataframe
        #  -1 : similar name (case-wise) or use itself
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('datetime', None),

        # Possible values below:
        #  None : column not present
        #  -1 : look for a similar name (case-wise) or use itself
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', 6),
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]

    def __init__(self):
        super(PandasData, self).__init__()

        # support column names from the pandas dataframe
        colnames = list(self.p.dataname.columns.values)
        self._colmapping = dict()

        # Build the column mappings to internal fields in advance
        for datafield in self.datafields:
            defmapping = getattr(self.params, datafield)
            self._colmapping[datafield] = defmapping

            if defmapping is None:
                continue

            if isinstance(defmapping, six.string_types):
                # specific name specified ... nothing else to do
                continue

            if isinstance(defmapping, six.integer_types):
                if defmapping >= 0:
                    # integer >= 0 ... specific colum
                    continue

                # -1 (or negative in general)
                # remove it and look for similar name or self
                self._colmapping.pop(datafield)

                # look for a similar name
                for colname in colnames:
                    if datafield.lower() == colname.lower():
                        self._colmapping[datafield] = colname
                        break

                if datafield not in self._colmapping:
                    # not yet there ... use self
                    self._colmapping[datafield] = datafield

    def start(self):
        # reset the length with each start
        self._idx = -1

    def _load(self):
        self._idx += 1

        if self._idx >= len(self.p.dataname):
            # exhausted all rows
            return False

        # Set the standard datafields
        for datafield in self.datafields[1:]:
            colindex = self._colmapping[datafield]
            if colindex is None:
                # datafield signaled as missing in the stream: skip it
                continue

            # get the line to be set
            line = getattr(self.lines, datafield)

            # indexing for pandas: 1st is colum, then row
            line[0] = self.p.dataname[colindex][self._idx]

        # datetime conversion
        coldtime = self._colmapping[self.datafields[0]]

        if coldtime is None:
            # standard index in the datetime
            tstamp = self.p.dataname.index[self._idx]
        else:
            # it's in a different column ... use standard column index
            tstamp = self.p.dataname.index[coldtime][self._idx]

        # convert to float via datetime and store it
        dt = tstamp.to_datetime()
        dtnum = date2num(dt)
        self.lines.datetime[0] = dtnum

        # Done ... return
        return True
