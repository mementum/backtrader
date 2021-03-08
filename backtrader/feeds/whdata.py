from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import struct

from backtrader import feed,date2num


class WHData(feed.DataBase):
    '''
    Support for `文华财经`_ binary on-disk files for
    both daily and intradaily formats.

    Note:

      - ``dataname``: to file or open file-like object

        If a file-like object is passed, the ``timeframe`` parameter will be
        used to determine which is the actual timeframe.

        Else the file extension (``.fd`` for daily and ``.min`` for intraday)
        will be used.
    '''

    def start(self):
        super(WHData, self).start()

        self.barsize = 4*9
        self.barfmt = '<I8f'

        self.f = None
        if hasattr(self.p.dataname, 'read'):
            # A file has been passed in (ex: from a GUI)
            self.f = self.p.dataname
        else:
            self.f = open(self.p.dataname, 'rb')
        
        bts = self.f.read(4)
        self.count = int.from_bytes(bts, byteorder='little')


    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None


    def _load(self):
        if self.f is None:
            return False

        # Let an exception propagate to let the caller know
        bardata = self.f.read(self.barsize)
        if not bardata:
            return False

        # ('timestamp','open','close','high','low','volume','openinterest','settlement','rate')
        bdata = struct.unpack(self.barfmt, bardata)

        dt = datetime.datetime.fromtimestamp(bdata[0])

        self.lines.datetime[0] = date2num(dt)

        self.lines.open[0] = bdata[1]
        self.lines.high[0] = bdata[3]
        self.lines.low[0] = bdata[4]
        self.lines.close[0] = bdata[2]
        self.lines.volume[0] = bdata[5]
        self.lines.openinterest[0] = bdata[6]

        return True

