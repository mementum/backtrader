# drawdown analyzer
class Drawdown_A(bt.Analyzer):
    '''This analyzer calculates trading system drawdowns stats such as drawdown values in %s and in
    dollars, max drawdown in %s and in dollars, drawdown length and drawdown max length

    Params:

      - no params are used

    Methods:

      - get_analysis

        Returns a dictionary with dradown stats as values, the following keys are available:

        'm' - drawdown value in money
        'p' - drawdown value in %s
        'max_m' - max drawdown value in money
        'max_p' - max drawdown value in %s
        'length' - drawdown length in bars
        'max_length' - max drawdown lentgh in bars
    '''

    def __init__(self):
        self.dd = {}
        self.dd['max_p'] = 0.0
        self.dd['max_m'] = 0.0
        self.dd['length'] = 0
        self.dd['max_length'] = 0
        self._maxvalue = self.strategy.broker.getvalue()

    def next(self):
        # get current broker value & upadet max broker value if necessary
        value = self.strategy.broker.getvalue()
        self._maxvalue = max(self._maxvalue, value)

        # calculate current drawdown values
        self.dd['m'] = value - self._maxvalue
        self.dd['p'] = self.dd['m'] / self._maxvalue * 100.0

        # calculate current max drawdown values
        self.dd['max_m'] = min(self.dd['max_m'], self.dd['m'])
        self.dd['max_p'] = min(self.dd['max_p'], self.dd['p'])

        # calculate current drawdown length
        if self.dd['m'] != 0:
            self.dd['length'] += 1
        else:
            self.dd['length'] = 0

        # calculate max drawdown length
        self.dd['max_length'] = max(self.dd['max_length'], self.dd['length'])

    def get_analysis(self):
        return self.dd
