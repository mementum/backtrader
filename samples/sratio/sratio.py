#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import itertools
import math
import operator
import sys


if sys.version_info.major == 2:
    map = itertools.imap


def average(x):
    return math.fsum(x) / len(x)


def variance(x):
    avgx = average(x)
    return list(map(lambda y: (y - avgx) ** 2, x))


def standarddev(x):
    return math.sqrt(average(variance(x)))


def run(pargs=None):
    args = parse_args(pargs)

    returns = [args.ret1, args.ret2]
    retfree = args.riskfreerate

    print('returns is:', returns, ' - retfree is:', retfree)

    # Directly from backtrader
    retfree = itertools.repeat(retfree)
    ret_free = map(operator.sub, returns, retfree)  # excess returns
    ret_free_avg = average(list(ret_free))  # mean of the excess returns
    print('returns excess mean:', ret_free_avg)
    retdev = standarddev(returns)  # standard deviation
    print('returns standard deviation:', retdev)
    ratio = ret_free_avg / retdev  # mean excess returns  / std deviation
    print('Sharpe Ratio is:', ratio)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample Sharpe Ratio')

    parser.add_argument('--ret1', required=False, action='store',
                        type=float, default=0.023286,
                        help=('Annual Return 1'))

    parser.add_argument('--ret2', required=False, action='store',
                        type=float, default=0.0257816485323,
                        help=('Annual Return 2'))

    parser.add_argument('--riskfreerate', required=False, action='store',
                        type=float, default=0.01,
                        help=('Risk free rate (decimal) for the Sharpe Ratio'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    run()
