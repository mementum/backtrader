#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# This 'kelly.py' module was written by Richard O'Regan (London) September 2017
#
###############################################################################
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


from backtrader import Analyzer
from backtrader.mathsupport import average
from backtrader.utils import AutoOrderedDict


class Kelly(Analyzer):
    '''Kelly formula was described in 1956 by J. L. Kelly, working at Bell Labs.

    It is used to determine the optimal size of a series of bets (or trades).
    The optimal size is given as a percentage of the account value.

    Caution: Kellys works optimally for systems that do not change over time.
    e.g. mechanical systems, tossing a coin, rolling a dice or for a casino,
    the spin of a roulette wheel.
    Whereas with trading systems. They are not fixed, and can work for a period
    of time and then stop working due to market conditions.
    Continuing to use Kelly's optimal percent to bet with, could incur heavy
    losses. I'm speaking from personal experience here! :)

    LESSON: Kelly percent is optimal providing your system edge remains
    working. The catch is, assume no system edge remains forever. Prepare for
    your system to stop working over time. Markets change.

    I personally find Kellys a useful measure for comparing systems.

    The formula:

        K = W - [(1 - W) / R]

    K = Kelly optimal percent
    e.g. 0.156 = 15.6 percent of account was optimal bet size
    (based on the historical trades your system generated).

    W = Win rate
    e.g. 0.6 (= 60%)
    Determined by counting profitable trades made.

    R = Win/Loss ratio
    e.g. 1.5 = Winners were on average 1.5 x losers
    Determined by taking average of all winners & average of all losers.

    Because R and W are determined from trades the strategy generates when
    run, there needs to be at least 1 winner and 1 loser. Otherwise 'None'
    is returned.

    Note: A negative Kelly percent e.g. -1.16 or -0.08, means the strategy lost
    money. The sign is important here. The actual value does not give any useful
    information as far as I can see.

    Methods:

      - get_analysis

        Returns a dictionary with keys "kellyPercent"

    [This 'kelly.py' module was coded by Richard O'Regan (UK) September 2017.]
    '''


    def create_analysis(self):
        '''Replace default implementation to instantiate an AutoOrdereDict
        rather than an OrderedDict'''
        self.rets = AutoOrderedDict()

    def start(self):
        super().start()   # Call parent class start() method
        self.pnlWins = list()       # Create list to hold winning trades
        self.pnlLosses = list()     # Create list to hold losing trades

    def notify_trade(self, trade):
        if trade.status == trade.Closed:  # i.e. trade had both an entry & exit
        # Note: for trades that scratch (=breakeven), i.e. a trade has exactly
        # $0 or 0 points profits. Should they be classed as a winner or loser?
        # Or perhaps create a seperate category for 'breakeven'?
        # On balance it probably doesn't make much difference.

        # If we class as a win, the win percent will increase but the average
        # win will decrease, i.e. maths balances out. Vice versa with losers.

        # I notice Backtrader assumes the same default, as used in
        # modules such as 'tradeanalyzer.py'

        # Likewise I will choose to class trades >=0 as winners.

            # Trades >=0 classed as profitable
            if trade.pnlcomm >=0:
                # Trade made money -> add to win list
                self.pnlWins.append(trade.pnlcomm)
            else:
                # Trade lost money -> add to losses list
                self.pnlLosses.append(trade.pnlcomm)


    def stop(self):
        # There must be at least one winning trade and one losing trade to
        # Calculate Kelly percent. Else get a division by zero error.
        if len(self.pnlWins) > 0 and len(self.pnlLosses) > 0:

            # Calculate average wins and losses
            avgWins = average(self.pnlWins)
            avgLosses = abs(average(self.pnlLosses))  # Remove the -ve sign
            winLossRatio = avgWins / avgLosses

            # Check winLoss ratio not 0 else division by zero later.
            # BT convention is to class trades with profit >=0 as a winner.
            # A rare bug can occur if all winners have value of 0.
            if winLossRatio == 0:
                kellyPercent = None   # Because average of winners were 0.

            else:
                # Calculate probability of winning from our data.
                # Number of wins divide by number of trades.
                numberOfWins = len(self.pnlWins)
                numberOfLosses = len(self.pnlLosses)
                numberOfTrades = numberOfWins + numberOfLosses
                winProb = numberOfWins / numberOfTrades
                inverse_winProb = 1 - winProb

                # Now calculate Kelly percentage
                # i.e. optimal percent of account to risk on each trade.
                kellyPercent = winProb - (inverse_winProb / winLossRatio)

        else:
            kellyPercent = None  # Not enough information to calculate.

        self.rets.kellyPercent = kellyPercent
