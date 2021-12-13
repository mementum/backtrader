from datetime import date
import datetime
import csv
import os.path
import sys


from enum import Enum

class PastTransaction:
    transactionType: str
    transactionDate : date
    amount: int
    price: float

    def __init__(self, tt, td, am, pr):
        self.transactionType = tt
        self.transactionDate = td
        self.amount = int(float(am))
        self.price = float(pr)

class TransactionsLoader:
    
    def Load(symbol):
        transactions_ = []
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, '../../Transactions')

        header = True
        with open(os.path.join(datapath,symbol)  + '.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                if header == False:
                    transactions_.append(PastTransaction(row[0], datetime.datetime.strptime(row[1], '%m/%d/%Y'), row[3], row[2]))
                header = False

        return transactions_


if __name__ == '__main__':
    TransactionsLoader.Load('ICCM.TA')