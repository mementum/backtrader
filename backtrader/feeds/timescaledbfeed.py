from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import backtrader.feed as feed
from backtrader.utils import date2num
import datetime as dt


TIMEFRAMES = dict(
    (
        (bt.TimeFrame.Seconds, 'seconds'),
        (bt.TimeFrame.Minutes, 'minutes'),
        (bt.TimeFrame.Days, 'days'),
        (bt.TimeFrame.Weeks, 'weeks'),
        (bt.TimeFrame.Months, 'months'),
        (bt.TimeFrame.Years, 'years'),
    )
)


class TimeScaleDB(feed.DataBase):
    frompackages = (
        ('psycopg2', 'connect'),
    )

    params = (
        ('host', 'localhost'),
        ('port', '5432'),
        ('username', None),
        ('password', None),
        ('database', None),

        ('dataname', None),
        ('timeframe', bt.TimeFrame.Days),
        ('compression', 1),
        ('fromdate', None),
        ('todate', None),
        ('sessionstart', None),
        ('datestart', None),
        ('tz', None),

        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
    )

    def start(self):
        # Prepare timeframe statement for query
        tf = '{multiple} {timeframe}'.format(
            multiple=(self.p.compression if self.p.compression else 1),
            timeframe=TIMEFRAMES.get(self.p.timeframe, 'days'))

        # Prepare timezone statements for query
        set_tz = ''
        at_tz = ''
        if self.p.tz:
            set_tz += f"SET TIME ZONE '{self.p.tz}';"
            at_tz += f"AT TIME ZONE '{self.p.tz}'"

        # Prepare origin argument for query
        origin = ''
        if self.p.datestart or self.p.sessionstart > dt.time(0):
            origin += ', TIMESTAMP '
            origin += f"'{self.p.datestart or '2000-01-01'} "
            origin += f"{self.p.sessionstart or '00:00:00'}'"

        # Add sessionstart to date limits if applicable
        fromdate = self.p.fromdate
        if self.p.sessionstart and fromdate:
            fromdate = dt.datetime.combine(fromdate, self.p.sessionstart)
        todate = self.p.todate
        if self.p.sessionstart and todate:
            todate = dt.datetime.combine(todate, self.p.sessionstart)
        
        # Prepare WHERE statement for query
        period = ''
        if fromdate or todate:
            period += 'WHERE time '
        if fromdate:
            period += f">= '{fromdate}'"
        if todate:
            if fromdate:
                period += ' AND time '
            period += f"< '{todate}'"

        # Assemble query
        qstr = f"""
            {set_tz}
            SELECT time_bucket('{tf}', time::TIMESTAMP {origin}) {at_tz} AS bucket, 
            FIRST(open, time) AS open, 
            MAX(high) AS high,
            MIN(low) AS low,
            LAST(close, time) AS close,
            SUM(volume) AS volume
            FROM {self.p.dataname}
            {period}
            GROUP BY bucket
            ORDER BY bucket
        """

        # Open a database connection, run query, get results
        conn = psycopg2.connect(database=self.p.database,
                                host=self.p.host,
                                user=self.p.username,
                                password=self.p.password,
                                port=self.p.port)
        cursor = conn.cursor()
        cursor.execute(qstr)
        dbars = cursor.fetchall()
        cursor.close()

        self.biter = iter(dbars)
        super().start()

    def _load(self):
        try:
            bar = next(self.biter)
        except StopIteration:
            return False

        self.l.datetime[0] = date2num(bar[self.p.datetime])
        self.l.open[0] = bar[self.p.open]
        self.l.high[0] = bar[self.p.high]
        self.l.low[0] = bar[self.p.low]
        self.l.close[0] = bar[self.p.close]
        self.l.volume[0] = bar[self.p.volume]

        return True
