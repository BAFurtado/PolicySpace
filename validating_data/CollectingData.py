# Data to collect for period 2000-2010
# GDP by municipality?
# Inflation
# Unemployment
# Basic Null Hypothesis: testing redistribution of taxes using RULES of FPE, FPM
# TODO: put together a table of actual data, similar to that of the output of the model

import matplotlib.pyplot as plt
import pandas as pd
from parameters import states_on_process
plt.style.use('fivethirtyeight')

inflation = pd.read_csv('validating_data/inflation.csv', delimiter=';')
inflation.data = pd.to_datetime(inflation.data, format='%Y-%m')

# plt.plot(inflation.data, inflation.inflation)
# plt.show()

unemployment = pd.read_csv('validating_data/unemployment.csv', delimiter=';')
unemployment.data = pd.to_datetime(unemployment.data, format='%Y-%m')
# plt.plot(unemployment.data, unemployment.unemployment)
# plt.show()

pib = pd.read_csv('validating_data/pib.csv', delimiter=';')
pib = pib.set_index('cod').T
pib.index = pd.to_datetime(pib.index, format='%Y')

rec_trib = pd.read_csv('validating_data/receitas_brutas_2014.csv', delimiter=';')

mun = ['5300108', '5217609', '5205497', '5219753', '5215231', '5208004', '5221858', '5200258', '5215603', '5212501']
mun_n = [5300108, 5217609, 5205497, 5219753, 5215231, 5208004, 5221858, 5200258, 5215603, 5212501]

for i in mun_n:
    plt.plot(pib.index, pib[i])
plt.legend(loc='best', labels=mun)
locs, labels = plt.yticks(fontsize=6)
plt.yticks(locs, map(lambda x: 'R$ {:,.0f}'.format(x), locs))
plt.savefig('../pib.png', dpi=300)
plt.show()

# idhm (already READ at generator module)
idhm = pd.read_csv('InputData/idhm_1991_2010.txt', sep=",",
                   header=0, decimal='.').apply(pd.to_numeric, errors='coerce')
idhm = idhm[idhm.year != 1991]
for i in mun:
    temp = idhm[idhm['cod_mun'] == int(i)]
    plt.plot(temp.year, temp.idhm)
plt.legend(labels=mun, loc='best', ncol=4, fancybox=True, shadow=False, framealpha=.25)
plt.show()

# Read FPE indices from
# C:\Users\r1702898\Documents\Modelagem\MeusModelos\DadosReferencias\fpe.csv

fpm = dict()
for state in states_on_process:
    fpm[state] = pd.read_csv('InputData/fpm/%s.csv' % state, sep=",", header=0, decimal='.', encoding='latin1')

# [:2] == state_str}
states_codes = pd.read_csv("InputData/STATES_ID_NUM.csv", sep=";", header=0, decimal=',')

states_dict = dict()

for i in range(len(states_codes)):
    states_dict[states_codes.iloc[i]['codmun']] = states_codes.iloc[i]['nummun']

mun = ['5300108', '5217609', '5205497', '5219753', '5215231', '5208004', '5221858', '5200258', '5215603', '5212501']
data_to_plot = pd.DataFrame()
for m in mun:
    for each in states_on_process:
        if str(states_dict[each]) == m[:2]:
            data_to_plot = data_to_plot.append(fpm[each][fpm[each]['cod'] == float(m)])
            break

data_to_plot.ano = data_to_plot.ano.astype(int)
data_to_plot.ano = data_to_plot.ano.astype(str)

# Reading fpm_test to compare
t = pd.read_csv('ValidatingDAta/model_output.csv', sep=";", header=0, decimal='.', encoding='latin1')
t = t[['month', 'region_id', 'fpm']]
t = t.rename(columns={'fpm': 'fpm_modelo'})
t = t.rename(columns={'region_id': 'cod'})

def basic_plotting_scheme(dataframe, column_x='ano', column_y='fpm', kind='line'):

    labels = []
    fig, ax = plt.subplots()
    fig.set_size_inches(16, 12)
    for key, grp in dataframe.groupby(['cod']):
        labels.append(key)
        ax = grp.plot(ax=ax, kind=kind, x=column_x, y=column_y)
    lines, _ = ax.get_legend_handles_labels()
    ax.legend(lines, labels, loc='best')
    plt.xlabel('Anos', fontsize=8)
    plt.ylabel('Valores em Reais', fontsize=8)
    plt.title('Evolução treasure')
    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: '{:,.0f}'.format(x), locs))
    locs, labels = plt.xticks()
    plt.xticks(locs, map(lambda x: '{:.0f}'.format(x), locs))
    fig.savefig('../treasure.png', dpi=300)
    plt.show()

# Reading and concatenating xlsx
names = ['2013', '2014', '2015', '2016', '2013iptu', '2014iptu', '2015iptu', '2016iptu']
taxes = dict()
for each in names:
    taxes[each] = pd.read_excel('validating_data/iptu_e_receitas_trib_brutas.xlsx', each)
    #tax[each].set_index(['cod'], inplace=True)

tax = pd.DataFrame(columns=['cod'])
for each in names:
    tax = tax.merge(taxes[each], how='outer', on='cod')

tax.to_csv('validating_data/taxes.csv')

years = [2013, 2014, 2015, 2016]
sep = tax[tax.apply(lambda x: x['cod'] in mun_n, axis=1)]
sep_iptu = sep[['cod', 'iptu_2013', 'iptu_2014', 'iptu_2015', 'iptu_2016']]
sep_rec = sep[['cod', 'rec_trib_2013', 'rec_trib_2014', 'rec_trib_2015', 'rec_trib_2016']]
sep_iptu.columns=[2013, 2014, 2015, 2016]
sep_iptu = sep_iptu.dropna()
fig = plt.figure()
sep_iptu.T.plot()
labels=[]
plt.legend(loc='best', labels=mun_n)
locs, labels = plt.yticks(fontsize=6)
plt.yticks(locs, map(lambda x: 'R$ {:,.0f}'.format(x), locs))
locs, labels = plt.xticks()
plt.xticks(locs, map(lambda x: '{:.0f}'.format(x), locs))
plt.savefig('C:/Users/r1702898/Desktop/treasure.png', dpi=300)

sep_rec = sep[['cod', 'rec_trib_2013', 'rec_trib_2014', 'rec_trib_2015', 'rec_trib_2016']]
sep_rec = sep_rec.set_index(['cod'])
sep_rec.columns=[2013, 2014, 2015, 2016]
sep_rec = sep_rec.dropna()
sep_rec.T.plot()
labels=[]
plt.legend(loc='best', labels=sep_rec.index, fontsize=6)
locs, labels = plt.yticks(fontsize=6)
plt.yticks(locs, map(lambda x: 'R$ {:,.0f}'.format(x), locs))
locs, labels = plt.xticks(fontsize=6)
plt.xticks(locs, map(lambda x: '{:.0f}'.format(x), locs))
plt.savefig('../treasure.png', dpi=300)

#formatting
pd.options.display.float_format = '{:,.0f}'.format
sep_rec.index = sep_rec.index.map('{:.0f}'.format)