import os
import numpy as np
import pandas as pd
import glob

os.chdir(r'..\ValidatingData')

# Data that is available in the MODEL
final_columns = ['month', 'region_id', 'commuting', 'pop', 'gdp_region', 'regional_gini',
                 'regional_unemployment', 'qli_index', 'gdp_percapita', 'treasure', 'consumption',
                 'property', 'labor', 'firm', 'transaction', 'fpm']


# Convention. Year is going to be transformed in the last month of that year
# So, as the model starts in 2000 and usually goes to 2020. 2002 corresponds to month 35.
# Auxiliary function to transform current year in model's month timing
def to_month(year):
    if year == 2000:
        return 11
    else:
        return (year - 2000) * 12 + 11


def to_year(month):
    return month // 12 + 2000

# Create empty DataFrame to aggregate data to
real = pd.DataFrame(columns=['region_id'])

# Reading data
# PIB
pib = pd.read_csv('pib.csv', sep=';', decimal='.', header=0)

# Transforming years in months
pib.columns = ['region_id', '35', '47', '59', '71', '83', '95', '107', '119', '131', '143', '155', '167', '179']

# Initiating all 5570 municipalitites
real.region_id = pib.region_id

# Transforming columns names into rows
pib = pd.melt(pib, id_vars='region_id')
pib.columns = ['region_id', 'month', 'gdp_region']

real = real.merge(pib, how='outer', on=['region_id'])
real.gdp_region = pd.to_numeric(real.gdp_region, errors='coerce')
real.gdp_region = real.gdp_region * 1000
real.month = pd.to_numeric(real.month, errors='coerce')


# Reading states initials
states = pd.read_csv('../InputData/STATES_ID_NUM.csv', sep=';').codmun.T.tolist()

# Reading states FPM data
fpm = pd.DataFrame()
for state in states:
    read = pd.read_csv('../InputData/fpm/%s.csv' % state, sep=",", header=0, decimal='.', encoding='latin1')
    fpm = fpm.append(read, ignore_index=True, verify_integrity=True)

# Changing year to months
fpm = fpm[['ano', 'fpm', 'cod']]
fpm.ano = fpm.ano.apply(to_month)
fpm.columns = ['month', 'fpm', 'region_id']
fpm.month = fpm.month.astype(int)

real = pd.merge(real, fpm, how='outer', on=['region_id', 'month'])

# Reading Receitas Tributárias Brutas and IPTU and separating
treasure = pd.read_csv('taxes.csv', sep=';')

# Preparing IPTU
iptu = treasure[['cod', 'iptu_2013', 'iptu_2014', 'iptu_2015', 'iptu_2016']]
iptu.columns = ['region_id', '167', '179', '191', '203']
iptu = pd.melt(iptu, id_vars='region_id')
iptu.columns = ['region_id', 'month', 'iptu']
iptu.month = iptu.month.astype(int)

# Merging
real = pd.merge(real, iptu, how='outer', on=['region_id', 'month'])

# Preparing Rec. Trib. Brutas
treasure = treasure[['cod', 'rec_trib_2013', 'rec_trib_2014', 'rec_trib_2015', 'rec_trib_2016']]
treasure.columns = ['region_id', '167', '179', '191', '203']
treasure = pd.melt(treasure, id_vars='region_id')
treasure.columns = ['region_id', 'month', 'treasure']
treasure.month = treasure.month.astype(int)
treasure.region_id = treasure.region_id.astype(int)

real.region_id = real.region_id.astype(int)
real.month = real.month.astype(int)

real = pd.merge(real, treasure, how='outer', on=['region_id', 'month']).sort_values('month')

# Still have to download unemployment by RMs
# unemployment = pd.read_csv('unemployment.csv', delimiter=';')
# unemployment.data = pd.to_datetime(unemployment.data, format='%Y-%m')

# Incorporating IDHM 2000 2010
idhm = pd.read_csv('../InputData/idhm_1991_2010.txt', sep=",", header=0, decimal='.').apply(pd.to_numeric,
                                                                                            errors='coerce')
idhm = idhm[idhm.year != 1991]
idhm['month'] = idhm.year.apply(to_month)
idhm = idhm[['cod_mun', 'idhm', 'month']]
idhm.columns = ['region_id', 'idhm', 'month']

real = pd.merge(real, idhm, how='outer', on=['region_id', 'month']).sort_values('month')

# Reading POP
pop_men = pd.read_csv('../InputData/pop_men.csv', sep=";", header=0)
pop_women = pd.read_csv('../InputData/pop_women.csv', sep=";", header=0)

# Summing up pop by age and gender
pop_men['pop'] = pop_men.ix[:, pop_men.columns != 'cod_mun'].sum(axis=1)
pop_women['pop'] = pop_women.ix[:, pop_women.columns != 'cod_mun'].sum(axis=1)

# Keeping just totals
pop_men = pop_men[['cod_mun', 'pop']]
pop_women = pop_women[['cod_mun', 'pop']]

# Merging into one pop total (2000)
pop = pd.merge(pop_men, pop_women, on='cod_mun')
pop['pop'] = pop.pop_x + pop.pop_y
pop = pop[['cod_mun', 'pop']]
pop.columns = ['region_id', 'pop']
pop['month'] = 11

pop10 = pd.read_excel('pop2010.xlsx')
pop16 = pd.read_excel('estimativa_pop_2016.xlsx')
pop16['month'] = 203

pop = pd.merge(pop, pop10, how='outer', on=['region_id', 'month', 'pop']).astype(int).sort_values('month')
pop16.columns = ['pop', 'region_id', 'month']
pop = pd.merge(pop, pop16, how='outer', on=['region_id', 'month', 'pop'])

real = pd.merge(real, pop, how='outer', on=['region_id', 'month']).sort_values('month')

# Reading xlsx files of PNAD continua for unemployment variables and aggregating in a single Dataframe
# IMPORTANT: main RMs values for unemployment imposed for all municipalities in given state
list_u = glob.glob(r'C:\Users\r1702898\Documents\Modelagem\MeusModelos\DadosReferencias\PNADC_desemprego/*.*')
u = pd.DataFrame(columns=['state', 'month', 'unemployment'])
for i in range(len(list_u)):
    temp = pd.to_numeric(pd.read_excel(list_u[i], sheetname='1 - Tabela 1',
                                       skiprows=7, skip_footer=8, header=0)['Unnamed: 3'])
    temp2 = [146 + c * 3 for c in range(len(temp))]
    temp3 = [list_u[i][100:102] for x in range(len(temp2))]
    u = pd.concat([u, pd.DataFrame({'unemployment': temp, 'month': temp2, 'state': temp3})])

# Adjusting TYPEs
u.month = u.month.astype(str)
real.region_id = real.region_id.astype(str)
real['state'] = real['region_id'].str[:2]
real.month = real.month.astype(str)

# Merging
real = pd.merge(real, u, how='outer', on=['month', 'state'])

real = real[pd.notnull(real.region_id)]
real.region_id = real['region_id'].astype(float).astype(int)

# Replacing values for CAPITALS within RMs
list_c = glob.glob(r'..\PNADC_u_capitais/*.*')
c = pd.DataFrame(columns=['month', 'unemployment'])
names = pd.read_csv('../InputData/names_and_codes_municipalities.csv', sep=';')
for i in range(len(list_c)):
    temp = pd.to_numeric(pd.read_excel(list_c[i], sheetname='1 - Tabela 1',
                                       skiprows=7, skip_footer=8, header=0)['Unnamed: 3'])
    temp2 = [146 + c * 3 for c in range(len(temp))]
    if list_c[i].split('-')[1].split(' ')[3] == '':
        capital_name = list_c[i].split('-')[1].split(' ')[2]
    elif list_c[i].split('-')[1].split(' ')[3] == 'de':
        capital_name = 'Rio de Janeiro'
    else:
        capital_name = ' '.join(list_c[i].split('-')[1].split(' ')[2:4])
    temp0 = names.cod_mun[names.cod_name.str.upper() == capital_name.upper()].iloc[0]
    temp3 = [temp0 for x in range(len(temp2))]

    c = pd.concat([c, pd.DataFrame({'unemployment': temp, 'month': temp2, 'region_id': temp3})])

c.region_id = c.region_id.astype(int)
c.month = c.month.astype(int)
real.month = real.month.astype(float).astype(int)
real = pd.merge(real, c, how='outer', on=['region_id', 'month'])

real.loc[:, 'unemployment'] = None
real.loc[:, 'unemployment'] = real['unemployment'].fillna(real['unemployment_x'])
real.loc[:, 'unemployment'] = real['unemployment'].fillna(real['unemployment_y'])

real = real.drop(['unemployment_x', 'unemployment_y', 'state'], axis=1)
real.month = real.month.astype(float).astype(int)
real.region_id = real.region_id.astype(int)

# Complementing table with extra real data of Tax from 2000-2012
# Getting a sense of the file
trib = pd.ExcelFile(r'C:\Users\r1702898\Documents\Modelagem\MeusModelos\DadosReferencias/FINBRA_IPEA_RECEITAS_DESPESAS2000_2012.xls')
# parsing a single sheet
sheets = ['Receita2000_2', 'Receita2001_2', 'Receita2002_2', 'Receita2003_2', 'Receita2004_2', 'Receita2005_2',
          'Receita2006_2', 'Receita2007_2', 'Receita2008_2', 'Receita2009_2', 'Receita2010_2', 'Receita2011_2',
          'Receita2012_2']

trib2 = pd.DataFrame()
for each in sheets:
    temp = trib.parse(each)
    # Using current govenment income, instead of only tax incomes in order to include federal governmental transfers
    temp = temp[['Rec_Correntes', 'IPTU', 'ITBI', 'Cod_Municipio_Completo']]
    temp['month'] = to_month(int(each[-6:-2]))
    trib2 = trib2.append(temp)

trib2.loc[trib2['ITBI'] <= 0, 'ITBI'] = np.nan
trib2.loc[trib2['IPTU'] <= 0, 'IPTU'] = np.nan
trib2.loc[trib2['Rec_Correntes'] <= 0, 'Rec_Correntes'] = np.nan

trib2.columns=['treasure', 'iptu', 'itbi', 'region_id', 'month']

real2 = pd.merge(real, trib2, how='left', on=['region_id', 'month']).sort_values(['region_id', 'month'])

real2['treasure'] = real2['treasure_x'].fillna(real2['treasure_y'])
real2['iptu'] = real2['iptu_x'].fillna(real2['iptu_y'])

real2 = real2.drop(['treasure_x', 'treasure_y', 'iptu_x', 'iptu_y'], axis=1)

# Saving
real2.to_csv('real_data.csv', sep=';', decimal='.')

# Rereading from CSV to conform dtypes
# real2 = pd.read_csv('real_data_consolidada.csv', sep=';', decimal='.', dtype={'gdp_region': 'float'})
# real2 = real2.drop('Unnamed: 0', axis=1)
# pd.options.display.float_format = '{:,.2f}'.format

codes = pd.read_csv('../InputData/acps_mun_codes.csv', sep=';').cod_mun.tolist()
real_acps = real2[real2['region_id'].isin(codes)]
real_acps.to_csv('real_acps_min_data.csv', sep=';')
