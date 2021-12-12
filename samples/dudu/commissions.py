import backtrader as bt

class DegiroCommission(bt.CommInfoBase):
    params = (('per_share', 0.004), ('flat', 0.5),)

    def _getcommission(self, size, price, pseudoexec):
        return self.p.flat + abs(size) * self.p.per_share
