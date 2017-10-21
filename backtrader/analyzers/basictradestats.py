#######################################
# Code: Rich O'Regan  (London) Sep 2017
#######################################

import math
import numpy as np

from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict


class BasicTradeStats(Analyzer):
    '''
    Summary:

        Calculate popular statistics on all closed trades.
        Also calculates statistics on winning and losing trades seperately.
        Statistics include, percentage of winning trades, reward risk ratio
        and basic streak analysis.


    Params:

         - ``calcStatsAfterEveryTrade``: (default: ``False``)
         ### COMMENTS NEEDED ####

         - ``useStandardPrint``: (default: ``False``)
         ### COMMENTS NEEDED ####


    Methods:

      - get_analysis

        Returns a dictionary holding the statistics.


    Statistics calculated:

        From ALL trades:

            total   - number of all trades closed and open.

            open    - number of open trades.
                NOTE: Obvious point but worth reminding.If a trade is open,
                      it is not yet known if it will be a winner or loser.

            closed  - number of closed trades.


            - pnl

                total   - p&l of all trades combined.

                average - average p&l from every trade taken, won or lost.


            - stats

                profitFactor - total of all profit / total of all losses.

                winFactor   - number of trades won / number of trades lost.

                winRate   - percentage of winning trades (also called strike rate).

                rewardRiskRatio - average profit of winning trades
                                  / average loss from losing trades.


        From WON trades:

            closed  - number of closed trades.

            percent - winning trades as a percentage of all closed trades.


            - pnl

                total   - total p&l of only the winning trades.

                average - average p&l of winning trades.

                median  - median p&l of winning trades.

                max     - maximun p&l generated on a trade,
                          from set of all winning trades.


            - streak

                current - current length of winning streak (if any).

                max     - maximum length of winning streak that occurred.

                average - average length of winning streaks.

                median  - median length of winning streaks.


        From LOST trades:

            Includes stats from WON above but applied to losing trades.

    [This 'basictradedtats.py' was coded by Richard O'Regan (London) October 2017]
    '''

    # Declare parameters user can pass to this Analyzer..
    params = (
            # Run calculations once at end (fast) OR after every trade (slower)
            ('calcStatsAfterEveryTrade', False ),

            # Filter stats on long or short trades only..
            # 'all' = all trades
            # 'long' = long trades only
            # 'short' = short trades only
            ('filter', 'all'),

            # When .print() called
            # If True -> use standard BackTrader print() [this is verbose]
            # If False -> instead use my clearer table format..
            ('useStandardPrint', False),
            )


    def create_analysis(self):
        # Set up variables..

        # Variables hidden from user..

        # Depending on the input parameter user provides for 'filter',
        # append 'LONG' or 'SHORT' in table heading output to user.
        # Helps user identify the types of trades stats calculated on,
        # either long, short or all (i.e. both)..
        if self.p.filter == 'long':
            self._tableLongShort =  'LONG'  # Append 'LONG' to table heading..
        elif self.p.filter == 'short':
            self._tableLongShort =  'SHORT' # Append 'SHORT' to table heading..
        elif self.p.filter == 'all':
            self._tableLongShort =  'TRADES'  # Blank char appended to our table..
        else:
            raise Exception("Parameter 'filter' must be 'long', 'short', or" +
                            " 'all' not '%s'." % str(self.p.filter))

        self._all_pnl_list=[]    # hidden from user - all trades pnl.
        self._won_pnl_list=[]    # hidden from user - win trades pnl.
        self._lost_pnl_list=[]   # hidden from user - lost trades pnl.
        self._curStreak = None  # Current streak type [None, 'Won', 'Lost']
        self._wonStreak_list=[]    # Store each won streak in list..
        self._lostStreak_list=[]    # Store each loss streak in list..

        # Variables output to user..
        o = self.rets = AutoOrderedDict()   # Return user object..
        # Stats applied to all trades (winners and losers)..
        o.all.trades.total = 0
        o.all.trades.open = 0
        o.all.trades.closed = 0
        o.all.pnl.total = None
        o.all.pnl.average = None
        o.all.streak.zScore = None
        o.all.stats.profitFactor = None
        o.all.stats.winFactor = None
        o.all.stats.winRate = None
        o.all.stats.rewardRiskRatio = None
        o.all.stats.expectancyPercentEstimated = None
        o.all.stats.kellyPercent = None

        for each in ['won', 'lost']:
            oWL=self.rets[each]
            oWL.trades.closed = 0
            oWL.trades.percent = None
            oWL.pnl.total = None
            oWL.pnl.average = None
            oWL.pnl.median = None
            oWL.pnl.max = None
            oWL.streak.current = 0
            oWL.streak.max = None
            oWL.streak.average = None
            oWL.streak.median = None


    def calculate_statistics(self):
        # Calculate various statistics..
        # Applied to three groups;
        #   1) All trades
        #   2) Winning trades
        #   3) Losing trades

        # NOTE: To see for different types of trades, e.g. Long or Short,
        # simply run strategy with Long trades only, gather stats,
        # and then re-run with short trades only and gather stats.
        # A system that goes long and short can be simplified to two different
        # systems. likely parameters will be different also..

        # This method can be called either;
        #   1) After every completed trade, i.e. ran multiple times.
        #   2) Once at end after all trades completed.

        # Option 1) occurs if calcStatsAfterEveryTrade is set to True.
        # Option 2) occurs if calcStatsAfterEveryTrade is set to False.

        # NOTE: Final output after last trade will always be the same.
        # regardless of which option you use. The difference is that option 1)
        # allows your strategy to access these statistics whilst it is running.

        # Option 1)
        # Running after every trade is obviously slower but needed if your
        # strategy needs to know these statstics whilst running. i.e. may adapt
        # itself as profit and loss statistics change.
        # example1: as winning streak increases, bet more.
        # example2: if win rate drops to less than 50% (0.5) stop trading until
        # win rate picks back up to 70% (0.7)..

        # Option 2)
        # If strategy does not need to know these information, it will be
        # quicker to run statistics just once at the end. In which case
        # option 2 is quicker and more efficient.


        # Must be at least 1 trade to proceed..
        if self._all_pnl_list!=[]:

            # Set up 'pointers' to save typing long lines..
            oA=self.rets.all
            oW=self.rets.won
            oL=self.rets.lost
            oA.pnl.total = np.sum(self._all_pnl_list)
            oA.pnl.average = np.mean(self._all_pnl_list)

            # Calc stats seperately for winning and losing trades..
            for each in ['won', 'lost']:
                # Get our list. Either _won_pnl_list or _lost_pnl_list..
                pnlList = eval('self._' + str(each) + '_pnl_list')

                # Check list not empty, else can't calculate median e.t.c.
                if pnlList!=[]:
                    oWL=self.rets[each]
                    oWL.trades.closed = np.size(pnlList)
                    oWL.trades.percent = len(pnlList)/len(self._all_pnl_list)*100
                    oWL.pnl.total = np.sum(pnlList)
                    oWL.pnl.max = np.max(pnlList)
                    oWL.pnl.average = np.mean(pnlList)
                    oWL.pnl.median = np.median(pnlList)
                    # Streak calculations..
                    streak = eval('self._' + str(each) + 'Streak_list')
                    if streak!=[]:
                        oWL.streak.max = np.max(streak)
                        oWL.streak.average = np.mean(streak)
                        # Can only be integer. Cast from double/float to integer
                        oWL.streak.median = int(np.median(streak))

            # Calc key stats on ALL trades..
            oA.stats.winRate = oW.trades.percent
            # Can only calc following if at least 1 winner and 1 loser..
            if self._won_pnl_list!=[] and self._lost_pnl_list!=[]:
                oA.streak.zScore = self.zScore(oW.trades.closed,
                                               oL.trades.closed,
                                               len(self._wonStreak_list))
                oA.stats.profitFactor = (oW.pnl.total
                                                / (-1 * oL.pnl.total))
                oA.stats.winFactor = (oW.trades.closed
                                              / oL.trades.closed)
                oA.stats.rewardRiskRatio = (oW.pnl.average
                                           / (-1 * oL.pnl.average))
                oA.stats.expectancyPercentEstimated = (oA.pnl.average
                                               / (-1 * oL.pnl.average) * 100)
                oA.stats.kellyPercent = oA.pnl.average / oW.pnl.average * 100


    def preparation_pre_calculation(self, trade):
        # This code does the basic steps of sorting each trade into a winner or
        # loser list which is then used later by 'calculate_statistics()'.
        # It also sets up the lists for winner and losing streak analysis.

        # NOTE: the code here runs in linear n time. There should be little
        # reason to optimise. Better to optimise 'calculate_statistics()' as
        # this may be running every trade in exponential O^n time.
        # [If you don't know what n time or O^n times means, don't stress :) ]


        if trade.justopened:
            # Trade just opened, update number of trades..
            self.rets.all.trades.total += 1
            self.rets.all.trades.open += 1

        elif trade.status == trade.Closed:
            # Trade closed, updated number of trades closed..
            self.rets.all.trades.open += -1
            self.rets.all.trades.closed += 1

            # Put each trade pnl into different buckets (lists) depending if
            # they are winning or losing trades..
            pnl = trade.pnlcomm
            self._all_pnl_list.append(pnl)   # List of all win & losing trades.
            if pnl >= 0:
                # Current trade is a winner..
                self._won_pnl_list.append(pnl)  # List of all win trades

                # Update winning streak list..
                if self._curStreak=='Won':
                    # Previous trade was also a winner..
                    self.rets.won.streak.current+=1
                else:
                    # Previous trade was a loser..
                    self._curStreak='Won'
                    self._lostStreak_list.append(self.rets.lost.streak.current)
                    self.rets.lost.streak.current=0
                    self.rets.won.streak.current+=1
            else:
                # Current trade is a loser..
                self._lost_pnl_list.append(pnl)  # List of all losing trades

                # Update losing streak list..
                if self._curStreak=='Lost':
                    # Previous trade was also a loser..
                    self.rets.lost.streak.current+=1

                else:
                    # Previous trade was a winner..
                    self._curStreak='Lost'
                    self._wonStreak_list.append(self.rets.won.streak.current)
                    self.rets.won.streak.current=0
                    self.rets.lost.streak.current+=1


    def notify_trade(self, trade):

        longMatch = trade.long and self.p.filter == 'long'
        shortMatch = not trade.long and self.p.filter == 'short'
        allMatch = self.p.filter == 'all'

        if True in [longMatch, shortMatch, allMatch]:
            self.preparation_pre_calculation(trade)

            if self.p.calcStatsAfterEveryTrade:
                self.calculate_statistics()
        ### ROR - question about overide or filter (can we still access individual), also _name for Sharpe

    def stop(self):
        super().stop    # Check if we need this..         ########
        if not self.p.calcStatsAfterEveryTrade: self.calculate_statistics()
        self.rets._close()    # Check if we need this..   £££££££££####


    def zScore(self, wins, losses, streaks):
        '''
        Calculates the Z-Score of streaks of wins and losses from a trading system.

        If system has a significant Z score then it is potentially possible to
        exploit the system for extra profit.

        A negative Z score means that there are fewer streaks in the trading
        system than would be expected statistically. This means that winning
        trades tend to follow winning trades and that losing trades tend to
        follower losers.

        A positive Z score means that there are more streaks in the trading
        system than would be expected. This means that winners tend to follow
        losers and vice versa.

        A confidence level of 95% or above is generally regarded as significant
        enough to exploit the apparent non-randomness of streaks in a system.

        Z scores of above 1.96 and below -1.96 represent 95% confidence.
        i.e. Z scores less than 1.96 and greater than -1.96 e.g. 0.87 or -1.2,
        suggest that outcome of previous trade cannot be used successfully to
        predict (and therfore profit) from outcome of following trade.

        A score of 0.0 suggests trade outcome totally independent of previous
        trade outcome.


        THE CALCULATION:

            Z-Score = (n*(s - 0.5) - x)  /  ((x*(x - n))/(n - 1))^(1/2)

        Where:

            s = The total number of streaks in the sequence.
            w = The total number of winning trades in the sequence.
            L = The total number of losing trades in the sequence.
            n = w + L [i.e. total number of trades in the sequence.]
            x = 2*w*L


        CONFIDENCE LEVELS:

            z Score of 3.0  = 99.73%
            Z Score of 2.58 = 99.0%
            Z Score of 2.17 = 97.0%
            Z Score of 1.96 = 95.0%
            Z Score of 1.64 = 90.0%
            Z Score of 1.44 = 85.0%
            Z Score of 1.28 = 80.0%
            Z Score of 1.04 = 70.0%


        LIMITATIONS:

            The Z-Score does not take into account size of wins and losses in
            each trade of streak. Only binary outcomes considered, i.e. the
            trade either won or lost.
            Apparently Serial Correlation methods can deal with magnitude and
            therefore provide a more useful statistic than Z-Score.


        SOURCE OF INFORMATION:

            http://www.mypivots.com/dictionary/definition/233/z-score
            Maths probably came from book;
            The Mathematics of Money Management: Risk Analysis Techniques for
            Traders by Ralph Vince.

        [This 'Z-Score' function was coded by Richard O'Regan (London) October 2017]
        '''
        w = wins
        L = losses
        s = streaks
        n = w + L
        x = 2*w*L

        denominator = math.sqrt( (x*(x - n)) / (n - 1) )
        if denominator != 0:   # Avoid division by zero error..
            numerator = n*(s - 0.5) - x
            z = numerator/denominator
            return z

        # Denominator was zero, therefore can't calculate..
        return None


    def print(self, *args, **kwargs):
        '''
        Overide print method to display statistics to user in a
        more visually pleasing and space efficient table format.
        '''
        # NOTE: Since this code is probably just a one off for this Analyzer
        # It is not yet a flexible general purpose method to display any data
        # in any table.
        # It currently have half programmable and half hardwired functionality.
        # Should this nicer output need to be used in other modules, the
        # code could be modified to become general purpose.
        # For now time is short and I just need something specific that works:)

        # If user requests standard output, print using parent class..
        if self.p.useStandardPrint:
            super().print(*args, **kwargs)
            return
        # ..else override and make look nicer..!

        # Set up 'pointers' to save typing long lines..
        oAt=self.rets.all.trades
        oAp=self.rets.all.pnl
        oAs=self.rets.all.stats
        oAk=self.rets.all.streak
        oWt=self.rets.won.trades
        oWp=self.rets.won.pnl
        oWk=self.rets.won.streak
        oLt=self.rets.lost.trades
        oLp=self.rets.lost.pnl
        oLk=self.rets.lost.streak
        dpsf=self.dpsf  # Decimal Place & Significant Figure formatting..

        #oWt.percent=None  ### ROR remove

        # Structure for output
        # List of dicts  #### improve comenting
        d = [
            {'rowType':'table-top'},
            {'rowType':'row-title', 'data':
            ['' , 'ALL ' + self._tableLongShort,
            '', self._tableLongShort + ' WON', self._tableLongShort + ' LOST']},

            {'rowType':'table-seperator'},
            {'rowType':'row-data', 'data':
            ['TRADES       open', dpsf(oAt.open),
            'TRADES          ', '', '']},
            #'%.2f' % oWt.percent if oWt.percent!=None else oWt.percent,
            #('%s' if oLt.percent is None else '%.2f') % oLt.percent]},

            {'rowType':'row-data', 'data':
            ['closed', dpsf(oAt.closed),
            'closed', dpsf(oWt.closed), dpsf(oLt.closed)]},

            {'rowType':'row-data', 'data':
            ['Win Factor', dpsf(oAs.winFactor, dp=2),
            '%', dpsf(oWt.percent, dp=2), dpsf(oLt.percent, dp=2)]},
            #['Win Factor','%.2f'% oAs.winFactor, '%',
            #'%.2f' % oWt.percent if oWt.percent!=None else oWt.percent,
            #('%s' if oLt.percent is None else '%.2f') % oLt.percent]},

            {'rowType':'table-seperator'},
            {'rowType':'row-data', 'data':
            ['PROFIT      total', dpsf(oAp.total),
            'PROFIT     total', dpsf(oWp.total), dpsf(oLp.total)]},

            {'rowType':'row-data', 'data':
            ['average', dpsf(oAp.average), 'average',
            dpsf(oWp.average), dpsf(oLp.average)]},

            {'rowType':'row-data', 'data':
            ['Profit Factor', dpsf(oAs.profitFactor, dp=2),
            'median', dpsf(oWp.median), dpsf(oLp.median)]},

            {'rowType':'row-data', 'data':
            ['Reward : Risk', dpsf(oAs.rewardRiskRatio, dp=2),
            'max', dpsf(oWp.max), dpsf(oLp.max)]},

            {'rowType':'table-seperator'},
            {'rowType':'row-data', 'data':
            ['STREAK    Z-Score', dpsf(oAk.zScore, dp=2),
            'STREAK   current', dpsf(oWk.current), dpsf(oLk.current)]},

            {'rowType':'row-data', 'data':
            ['', '',
            'max' , dpsf(oWk.max), dpsf(oLk.max)]},

            {'rowType':'row-data', 'data':
            ['OTHER            ', '',
            'average', dpsf(oWk.average), dpsf(oLk.average)]},

            {'rowType':'row-data', 'data':
            ['Expectancy %', dpsf(oAs.expectancyPercentEstimated, dp=1),
            'median', dpsf(oWk.median), dpsf(oLk.median)]},

            {'rowType':'row-data', 'data':
            ['Kelly %', dpsf(oAs.kellyPercent, dp=1),
            '', '', '']},

            #{'rowType':'row-data', 'data':
            #['Kelly %','%.1f'% oAs.kellyPercent,'','','']},

            {'rowType':'table-bottom'}
        ]

        s = self.displayTable(d)
        print(s)


    def fixedWidthText(self, string, nChars=15, align='centre'): # ,horzChar='═'):
        # Displayoutput string of exactly n chars, no more no less (for good formatting)..

        # Convert input to string incase it is not e.g. an int
        string = str(string)

        # Pad input string with space chars either side.
        # Enables us to easily justify 'left','right' e.t.c. by slicing..
        _s=' '*nChars + string + ' '*nChars

        if align=='left' or align=='l':
            return _s[nChars : nChars + nChars]

        elif align=='right' or align=='r':
            return _s[len(string):nChars+len(string)]

        elif align=='centre' or align=='center' or align=='c':
            startIndex = nChars - (int((nChars - len(string))/2))
            return _s[startIndex : startIndex + nChars]

        else:
            raise Exception("Parameter 'align' must be 'left', 'right', or 'center' not '%s'." % str(align))


    def displayTable(self, i):
        # Input is a list of dictionaries, the 5 column format hardwired to
        # run specifically with this method..

        fWT = self.fixedWidthText  # Shortcut to text formatting function.

        # Find out max width need for each of the columns.
        # This enables us to customise size of table cell and ensure data fits..

        cs=[0,0,0,0,0]  # Store size of columm for each of 5 columns..

        for d in i:
            # Check for data rows..
            if d['rowType'] in ['row-title','row-data','row-data2']:

                # Go thro each data cell and keep track of the max text length needed to display..
                for c in range(5):  # There are always 5 columns (hardwired)
                    _l = len(str(d['data'][c]))
                    if _l > cs[c]: cs[c]= _l

        # Display each row by joining table cells together with these chars..
        (x,rx,lx,v,h)=('╬','╣','╠','║','═')
        (sv, hx, srx)=(' '+v, h+x, h+'╣')

        s=''
        for d in i:
            # Check for table formating rows..
            if d['rowType']=='table-top':
                s+='╔═'+'═'*cs[0]+'╦'+'═'*cs[1]+'═╗'+'  ╔═'+'═'*cs[2]+'╦'+'═'*cs[3]+'═╦'+'═'*cs[4]+'═╗\n'
            if d['rowType']=='table-seperator':
                s+='╠═'+'═'*cs[0]+'╬'+'═'*cs[1]+'═╣'+'  ╠═'+'═'*cs[2]+'╬'+'═'*cs[3]+'═╬'+'═'*cs[4]+'═╣\n'
            if d['rowType']=='table-bottom':
                s+='╚═'+'═'*cs[0]+'╩'+'═'*cs[1]+'═╝'+'  ╚═'+'═'*cs[2]+'╩'+'═'*cs[3]+'═╩'+'═'*cs[4]+'═╝'

            # Check for data rows..
            if d['rowType']=='row-title':
                l = d['data']
                s+= (v + fWT(l[0],cs[0]) + sv + fWT(l[1],cs[1],'center') + sv + '  ' + v
                   + fWT(l[2],cs[2]) + sv + fWT(l[3],cs[3],'center')
                   + sv + fWT(l[4],cs[4],'center') + sv + '\n')

            if d['rowType']=='row-data':
                l = d['data']
                s+= (v + fWT(l[0],cs[0],'right') + sv + fWT(l[1],cs[1],'left') + sv + '  ' + v
                   + fWT(l[2],cs[2],'right') + sv + fWT(l[3],cs[3],'left')
                   + sv + fWT(l[4],cs[4],'left') + sv + '\n')

            if d['rowType']=='row-data2':
                l = d['data']
                s+= (v + fWT(l[0],cs[0],'center') + sv + fWT(l[1],cs[1],'left') + sv + '  ' + v
                   + fWT(l[2],cs[2],'right') + sv + fWT(l[3],cs[3],'left')
                   + sv + fWT(l[4],cs[4],'left') + sv + '\n')

        # Return a string representing nicely formated table..
        return s


    def dpsf(self, n=None, dp=None, sf=None):
        # Decimal Place & Significant Figure formatting..

        # Logic used to display numeric values neatly:
        # dp = decimal places
        # sf = significant figues

        # n value is None type, e.g. a variable passed that does
        # not have enough data to be initialised correctly..
        # Do not try to format a None type, will cause an exception,
        # instead pass it straight back..
        if n == None:
            return 'None'

        # If no dp or sf provided..
        # Display but allow space for sign
        #if dp == None and sf == None:
        #    if

        # If just dp
        # check i= None

        # If just sf
        # check s= None

        # If both, take the biggest
        # checks n= None

        # Keep alignment if positive or negative number
        # e.g. -1.23 -> '-1.23'
        # e.g. 1.45  -> ' 1.45'  extra space added so stays aligned..
        if n >= 0:
            return ' ' + str(n)
        else:
            return str(n)
