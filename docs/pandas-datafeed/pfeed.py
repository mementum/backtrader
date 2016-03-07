#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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

from backtrader.utils.py3 import filter, string_types, integer_types

from backtrader import date2num
import backtrader.feed as feed


class PandasData(feed.DataBase):
    '''
    The ``dataname`` parameter inherited from ``feed.DataBase`` is the pandas
    DataFrame
    '''

    params = (
        # Possible values for datetime (must always be present)
        #  None : datetime is the "index" in the Pandas Dataframe
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('datetime', None),

        # Possible values below:
        #  None : column not present
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]

    def __init__(self):
        super(PandasData, self).__init__()

        # these "colnames" can be strings or numeric types
        colnames = list(self.p.dataname.columns.values)
        if self.p.datetime is None:
            # datetime is expected as index col and hence not returned
            # add fake entry for the autodetection algorithm
            colnames.insert(0, 0)

        # try to autodetect if all columns are numeric
        cstrings = filter(lambda x: isinstance(x, string_types), colnames)
        colsnumeric = not len(cstrings)

        # Where each datafield find its value
        self._colmapping = dict()

        # Build the column mappings to internal fields in advance
        for i, datafield in enumerate(self.datafields):
            defmapping = getattr(self.params, datafield)

            if isinstance(defmapping, integer_types) and defmapping < 0:
                # autodetection requested
                if colsnumeric:
                    # matching names doesn't help, all indices are numeric
                    # use current colname index
                    self._colmapping[datafield] = colnames[i]

                else:
                    # name matching may be possible
                    for colname in colnames:
                        if isinstance(colname, string_types):
                            if datafield.lower() == colname.lower():
                                self._colmapping[datafield] = colname
                                break

                    if datafield not in self._colmapping:
                        # not yet there ... use current index
                        self._colmapping[datafield] = colnames[i]
            else:
                # all other cases -- used given index
                self._colmapping[datafield] = defmapping

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
