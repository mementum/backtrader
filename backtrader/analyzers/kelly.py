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

###############################################################################
#
# This kelly.py module written by Richard O'Regan x/September/2017
#
###############################################################################


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

from backtrader import Analyzer
from backtrader.mathsupport import average, standarddev
from backtrader.utils import AutoOrderedDict

class Kelly(Analyzer):
    '''Kelly formula was described in 1956 by J. L. Kelly, working at Bell Labs.

    It is used to determine the optimal size of a series of bets (or trades).
    The optimal size is given as a percentage of the account value.

    For example. Suppose Dick and Fanny have a bet. Dick makes a wager with Fanny.
    He says; "Let's toss a coin together. If it lands on heads,
    you must give me $1, but it it lands on tails, I will give you $2."

    Fanny has $100 in her purse.

    The formula:

      - SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit)

    The sqn value should be deemed reliable when the number of trades >= 30

    Methods:

      - get_analysis

        Returns a dictionary with keys "sqn" and "trades" (number of
        considered trades)

    '''


    def create_analysis(self):
        '''Replace default implementation to instantiate an AutoOrdereDict
        rather than an OrderedDict'''
        self.rets = AutoOrderedDict()

    def start(self):
        super().start()   # Call parent class start() method..
        self.pnlWins = list()       # Create list to hold winning trades
        self.pnlLosses = list()     # Create list to hold losing trades

    def notify_trade(self, trade):
        if trade.status == trade.Closed:   # i.e. trade had both an entry and exit

            # Note for trades that scratch (i.e. breakeven), should they be
            # classes as a winner or loser (or in their own seperate category?)
            # On balance it probably doesn't make much difference.
            # If a trade has exactly $0 or 0 points profit

            # If we class as a win, the win percent will increase but the average
            # win will decrease, i.e. maths balances out. Vice versa with losers.

            # Also in most situations, vast majority of trades after commisions
            # applied, will not result in exactly breakeven. Far more likely will
            # be a slight profit or loss even if close.

            if trade.pnlcomm >= 0:    # Trades >=0 classed as profitable
                self.pnlWins.append(trade.pnlcomm)    # Append to winner list
            else:
                self.pnlLosses.append(trade.pnlcomm)  # Append to loser lise

    def stop(self):

        # There must be at least one winning trade and one losing trade to
        # Calculate Kelly percent. Else get a division by zero error.
        if len(self.pnlWins) > 0 and len(self.pnlLosses) > 0:
            #pnl_av = average(self.pnl)
            #pnl_stddev = standarddev(self.pnl)
            #qqn = math.sqrt(len(self.pnl)) * pnl_av / pnl_stddev

            # Calculate average wins and losses
            avgWins = average(self.pnlWins)
            avgLosses = average(self.pnlLosses)
            winLossRatio = avgWins / avgLosses

            # Calculate probability of winning from our data
            # Number of wins divide by number of trades
            numberOfWins = len(self.pnlWins)
            numberOfTrades = (len(self.pnlWins) + len(self.pnlLosses))
            winProb = numberOfWins / numberOfTrades

            # Now calculate Kelly percentage
            # i.e. calculate optional percent of account to risk on each trade
            kellyPercent = winProb - ((1 - winProb) / winLossRatio)

        else:
            kellyPercent = None

        self.rets.kellyPercent = kellyPercent
        #self.rets.trades = self.count
