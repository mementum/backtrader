from . import Indicator, Highest, Lowest
import math

__all__ = ['Fisher']

class Fisher(Indicator):

    _nextforce = True

    lines = ('Fx',)
    params = (('period', 20),)

    _alpha = 0.33
    _alphaFish = 0.5

    def __init__(self):

        self._scaledPrev = 0
        self._FxPrev = 0

        self._h = Highest(self.data, period=self.p.period)
        self._l = Lowest(self.data, period=self.p.period)

        super(Fisher, self).__init__()

    def next(self):

        d = self.data[0]

        h = self._h[0]
        l = self._l[0]

        Fx = self.l.Fx

        scaled = 2 * ((d - l) / (h - l) - .5)
        scaled = self._alpha * scaled + (1-self._alpha) * (self._scaledPrev if len(Fx) > 1 else scaled)

        if scaled > 0.9999:
            scaled = 0.9999
        elif scaled < -0.9999:
            scaled = -0.9999

        self._scaledPrev = scaled

        Fx[0] = math.log((1 + scaled) / (1 - scaled))
        self._FxPrev = Fx[0] = self._alphaFish * Fx[0] + (1-self._alphaFish) * (self._FxPrev if len(Fx) > 1 else Fx[0])

