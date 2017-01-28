#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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

import datetime
import itertools

from .. import feed
from ..utils import date2num


class GenericCSVData(feed.CSVDataBase):
    '''
    Parses a CSV file according to the order and field presence defined by the
    parameters

    Specific parameters (or specific meaning):

      - ``dataname``: The filename to parse or a file-like object

      - The lines parameters (datetime, open, high ...) take numeric values

        A value of -1 indicates absence of that field in the CSV source

      - If ``time`` is present (parameter time >=0) the source contains
        separated fields for date and time, which will be combined

      - ``nullvalue``

        Value that will be used if a value which should be there is missing
        (the CSV field is empty)

      - ``dtformat``: Format used to parse the datetime CSV field

      - ``tmformat``: Format used to parse the time CSV field if "present"
        (the default for the "time" CSV field is not to be present)
    '''

    params = (
        ('nullvalue', float('NaN')),
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('tmformat', '%H:%M:%S'),

        ('datetime', 0),
        ('time', -1),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', 6),
    )

    def _loadline(self, linetokens):
        # Datetime needs special treatment
        dtfield = linetokens[self.p.datetime]
        dtformat = self.p.dtformat

        if self.p.time >= 0:
            # add time value and format if it's in a separate field
            dtfield += 'T' + linetokens[self.p.time]
            dtformat += 'T' + self.p.tmformat

        dt = datetime.datetime.strptime(dtfield, dtformat)
        self.lines.datetime[0] = date2num(dt)

        # The rest of the fields can be done with the same procedure
        for linefield in (x for x in self.getlinealiases() if x != 'datetime'):
            # Get the index created from the passed params
            csvidx = getattr(self.params, linefield)

            if csvidx is None or csvidx < 0:
                # the field will not be present, assignt the "nullvalue"
                csvfield = self.p.nullvalue
            else:
                # get it from the token
                csvfield = linetokens[csvidx]

            if csvfield == '':
                # if empty ... assign the "nullvalue"
                csvfield = self.p.nullvalue

            # get the corresponding line reference and set the value
            line = getattr(self.lines, linefield)
            line[0] = float(float(csvfield))

        return True


class GenericCSV(feed.CSVFeedBase):
    DataCls = GenericCSVData
