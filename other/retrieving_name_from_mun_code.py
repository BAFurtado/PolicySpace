# Given a municipality code, return name of ACP
import pandas as pd
import os
import sys


def retrieve(cod):
    acps = pd.read_csv('../acps_mun_codes.csv',
                       sep=';')
    return acps[acps.cod_mun.isin([int(cod)])].iloc[0]['ACPs']


if __name__ == '__main__':
    os.chdir('..')
    print(retrieve(sys.argv[1]))
