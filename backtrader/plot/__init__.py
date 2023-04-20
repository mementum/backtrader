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

import sys
import os

try:
    import matplotlib
except ImportError:
    raise ImportError(
        'Matplotlib seems to be missing. Needed for plotting support')
else:
    touse = 'TKAgg' if sys.platform != 'darwin' else 'MacOSX'

    #In headless mode
    import os
    if os.environ.get("DISPLAY") is None and os.environ.get("MPLBACKEND") is None:
        print('no display found. Using non-interactive Agg backend')
        touse = "Agg"

    try:
        if os.environ.get("MPLBACKEND") is None:
            matplotlib.use(touse)
    except:
        # if another backend has already been loaded, an exception will be
        # generated and this can be skipped
        pass


from .plot import Plot, Plot_OldSync
from .scheme import PlotScheme
