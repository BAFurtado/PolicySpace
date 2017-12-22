import os
import sys

import numpy as np
import pandas as pd

from other import retrieving_name_from_mun_code as retrieve

# # Use columns below for regional model:
final_columns = ['month', 'region_id', 'commuting', 'model_pop', 'model_gdp_region', 'model_gini', 'model_house_price',
                 'model_unemployment', 'model_qli_index', 'model_gdp_percapita', 'model_treasure', 'model_consumption',
                 'model_property', 'model_labor', 'model_firm', 'model_transaction', 'model_fpm']

months_with_data = [11, 23, 35, 47, 59, 71, 83, 95, 107, 119, 131, 143, 146, 149, 152, 155, 158, 161, 164, 167, 170,
                    173, 176, 179, 182, 185, 188, 191, 194, 197, 200, 203, 206, 215]


# Deleting previously saved CSV files
def cleaning():
    to_del = ['summary_results_acp.csv', 'resumo_mun_month.csv', 'general_median.csv']
    for i in to_del:
        if os.path.exists(i):
            os.remove(i)


# Rereading from CSV to conform dtypes
def load_real_data():
    real = pd.read_csv('real_acps_min_data.csv', sep=';')
    real = real.drop('Unnamed: 0', axis=1)

    # Rewriting columns names
    real.columns=['region_id', 'month', 'real_gdp_region', 'real_fpm', 'real_qli_index', 'real_pop',
                  'real_unemployment', 'real_transaction', 'real_treasure', 'real_property']
    return real


def load_regional_files_path(path):
    model_output_files = [os.path.join(dirpath, f)
                          for dirpath, dirnames, files in os.walk(path)
                          for f in files if f.startswith('temp_regional.csv')]
    return model_output_files


# Read each individual file from the model
def reading_txt(to_read, save=False):
    if os.path.getsize(to_read) != 0:
        model = pd.read_csv(to_read, sep=';', header=0, decimal='.')
        model.columns = final_columns

        if not save:
            # Limiting table to comparable fields
            model_s = model[['region_id', 'month', 'model_gdp_region', 'model_fpm', 'model_property',
                             'model_consumption', 'model_treasure', 'model_transaction', 'model_qli_index',
                             'model_pop', 'model_unemployment', 'model_labor', 'model_firm']]

            # Merging the tables
            return model_s

        else:
            model.to_csv('full_model_outputs.csv')
            print("Averages for all regions")
            print("Unemployment {:.02f}".format(np.mean(model.regional_unemployment)))
            print("Gini {:.02f}".format(np.mean(model.regional_gini)))
            print("QLI index {:.02f}".format(np.mean(model.qli_index)))
            print("Arrecadação {:.02f}".format(np.mean(model.treasure)))
    else:
        print("File is empty {}".format(to_read))


# Calculating proportions and means
def final_calculations(to_calculate, name=None):
    if os.path.exists('summary_results_acp.csv'):
        results = pd.read_csv('summary_results_acp.csv', sep=';')
    else:
        results = pd.DataFrame(columns=['acp',
                                        'real_fpm',
                                        'model_fpm',
                                        'real_property',
                                        'model_property',
                                        'real_transaction',
                                        'model_transaction',
                                        'real_prop_property_gdp',
                                        'model_prop_property_gdp',
                                        'real_prop_transaction_gdp',
                                        'model_prop_transaction_gdp'
                                        'real_prop_fpm_gdp',
                                        'model_prop_fpm_gdp',
                                        'model_prop_consumption_gdp',
                                        'model_consumption',
                                        'model_labor',
                                        'model_firm',
                                        'model_treasure',
                                        'model_prop_labor_gdp',
                                        'model_prop_firm_gdp'])

    # Calculate proportions gdp and total
    # REAL TREASURE represents municipalities tax received (receitas tributárias),
    # not total available funds (receitas orçamentárias)
    # MODEL TREASURE include FPM (which is a TRANSFER). Received total taxes should be deduced of FPM
    to_calculate['real_prop_fpm_gdp'] = to_calculate['real_fpm'] / to_calculate['real_gdp_region']
    to_calculate['real_prop_property_gdp'] = to_calculate['real_property'] / to_calculate['real_gdp_region']
    to_calculate['real_prop_treasure_gdp'] = to_calculate['real_treasure'] / to_calculate['real_gdp_region']
    to_calculate['real_prop_transaction_gdp'] = to_calculate['real_transaction'] / to_calculate['real_gdp_region']
    to_calculate['model_prop_fpm_gdp'] = to_calculate['model_fpm'] / to_calculate['model_gdp_region']
    to_calculate['model_prop_property_gdp'] = to_calculate['model_property'] / to_calculate['model_gdp_region']
    to_calculate['model_prop_treasure_gdp'] = to_calculate['model_treasure'] / to_calculate['model_gdp_region']
    to_calculate['model_prop_transaction_gdp'] = to_calculate['model_transaction'] / to_calculate['model_gdp_region']
    to_calculate['model_prop_consumption_gdp'] = to_calculate['model_consumption'] / to_calculate['model_gdp_region']
    to_calculate['model_prop_firm_gdp'] = to_calculate['model_firm'] / to_calculate['model_gdp_region']
    to_calculate['model_prop_labor_gdp'] = to_calculate['model_labor'] / to_calculate['model_gdp_region']
    to_calculate['real_prop_property_total'] = to_calculate['real_property'] / to_calculate['real_treasure']
    to_calculate['real_prop_transaction_total'] = to_calculate['real_transaction'] / to_calculate['real_treasure']
    to_calculate['real_prop_fpm_total'] = to_calculate['real_fpm'] / to_calculate['real_treasure']
    to_calculate['model_prop_labor_total'] = to_calculate['model_labor'] / to_calculate['model_treasure']
    to_calculate['model_prop_firm_total'] = to_calculate['model_firm'] / to_calculate['model_treasure']
    to_calculate['model_prop_consumption_total'] = to_calculate['model_consumption'] / to_calculate['model_treasure']
    to_calculate['model_prop_property_total'] = to_calculate['model_property'] / to_calculate['model_treasure']
    to_calculate['model_prop_transaction_total'] = to_calculate['model_transaction'] / to_calculate['model_treasure']
    to_calculate['model_prop_fpm_total'] = to_calculate['model_fpm'] / to_calculate['model_treasure']

    # To add in pandas DataFrame use append([dict()])
    # Retrieving name of ACP to add to results' table
    if name is None:
        temp_name = retrieve.retrieve(int(to_calculate[~to_calculate.model_treasure.isnull()].iloc[0]['region_id']))
    else:
        temp_name = name

    results = results.append([{'acp': temp_name,
                               'real_gdp_region':  np.mean(to_calculate.real_gdp_region),
                               'model_gdp_region': np.mean(to_calculate.model_gdp_region),
                               'real_treasure': np.mean(to_calculate.real_treasure),
                               'model_treasure': np.mean(to_calculate.model_treasure),
                               'real_prop_fpm_gdp': np.mean(to_calculate.real_prop_fpm_gdp),
                               'model_prop_fpm_gdp': np.mean(to_calculate.model_prop_fpm_gdp),
                               'real_prop_property_gdp': np.mean(to_calculate.real_prop_property_gdp),
                               'model_prop_property_gdp': np.mean(to_calculate.model_prop_property_gdp),
                               'real_prop_transaction_gdp': np.mean(to_calculate.real_prop_transaction_gdp),
                               'model_prop_transaction_gdp': np.mean(to_calculate.model_prop_transaction_gdp),
                               'real_prop_treasure_gdp': np.mean(to_calculate.real_prop_treasure_gdp),
                               'model_prop_treasure_gdp': np.mean(to_calculate.model_prop_treasure_gdp),
                               'real_prop_property_total': np.mean(to_calculate.real_prop_property_total),
                               'model_prop_property_total': np.mean(to_calculate.model_prop_property_total),
                               'real_prop_transaction_total': np.mean(to_calculate.real_prop_transaction_total),
                               'model_prop_transaction_total': np.mean(to_calculate.model_prop_transaction_total),
                               'real_prop_fpm_total': np.mean(to_calculate.real_prop_fpm_total),
                               'model_prop_fpm_total': np.mean(to_calculate.model_prop_fpm_total),
                               'real_property': np.mean(to_calculate.real_property),
                               'model_property': np.mean(to_calculate.model_property),
                               'real_transaction': np.mean(to_calculate.real_transaction),
                               'model_transaction': np.mean(to_calculate.model_transaction),
                               'real_fpm': np.mean(to_calculate.real_fpm),
                               'model_fpm': np.mean(to_calculate.model_fpm),
                               'model_prop_consumption_gdp': np.mean(to_calculate.model_prop_consumption_gdp),
                               'model_prop_labor_gdp': np.mean(to_calculate.model_prop_labor_gdp),
                               'model_prop_firm_gdp': np.mean(to_calculate.model_prop_firm_gdp),
                               'model_prop_labor_total': np.mean(to_calculate.model_prop_labor_total),
                               'model_prop_firm_total': np.mean(to_calculate.model_prop_firm_total),
                               'model_prop_consumption_total':  np.mean(to_calculate.model_prop_consumption_total),
                               'model_consumption': np.mean(to_calculate.model_consumption),
                               'model_firm': np.mean(to_calculate.model_firm),
                               'model_labor': np.mean(to_calculate.model_labor)
                               }])

    # Save summary each time it is calculated for each individual ACP
    pd.options.display.float_format = '{:,.4f}'.format
    results.replace(np.inf, np.nan, inplace=True)
    results = results.groupby(by='acp').agg('mean')
    results = results.reset_index()
    results.to_csv('summary_results_acp.csv', sep=';', index=False)

    # Return the proportions with all municipalities
    return to_calculate


# Reads and request calculations for each file
def feeding_files(files, real_i):
    # temp accumulates all data
    temp = pd.DataFrame()
    for each in files:
        temp = temp.append(reading_txt(each))
        # Separately calculate for each individual file and append it to file
        # In the end, the saved file from
        temp2 = pd.DataFrame()
        temp2 = temp2.append(reading_txt(each))
        temp_real = real_i[real_i.region_id.isin(temp2.region_id.unique())]
        temp2 = pd.merge(temp_real, temp2, how='outer', on=['region_id', 'month'])
        final_calculations(temp2)

    temp[temp['model_gdp_region'] == 0] = None
    real_i = pd.merge(real_i, temp, how='outer', on=['region_id', 'month']).sort_values(['region_id', 'month'])

    return final_calculations(real_i, 'total')


# Continuing modeling with results. Preparing for validation_tentative
# Starting with general data. Consumption and inflation
# Reading real data by month
def read_real_general():
    real_general = pd.read_excel('inflation.xlsx')
    real_consumption = pd.read_excel('consumo_familias_k.xlsx')
    real_general = pd.merge(real_general, real_consumption, how='outer', on='month')
    return real_general


def load_model_general(path):
    # Reading general inflation from the model
    model_output_files_g = [os.path.join(dirpath, f)
                            for dirpath, dirnames, files in os.walk(path)
                            for f in files if f.startswith('temp_stats.csv')]
    # Columns of GENERAL results
    cols = ['month', 'model_price_index', 'model_gdp_index', 'model_gdp_growth', 'model_unemployment',
            'model_avg_workers', 'model_fam_wealth', 'model_fam_savings', 'model_firms_wealth', 'model_firms_profit',
            'model_gini', 'model_fam_consumption', 'model_inflation', 'model_qli_index']
    return model_output_files_g, cols


# Averaging all runs monthly inflation
def concatenating_columns(model_output_files_g, cols):
    temp1 = pd.DataFrame()
    for each in model_output_files_g:
        t = pd.read_csv(each, sep=';', decimal='.', header=None)
        t.columns = cols
        temp1 = temp1.append(t)

    #temp1.loc[temp1.month=='\ufeff0'] = 0
    temp1.month = temp1.month.astype(int)
    temp1 = temp1.groupby(by=['month']).agg('median')
    return temp1


def saving(resumo, real_general, files, cols):
    resumo = resumo.dropna(axis=0, how='all')

    # Include ACPs title
    resumo.region_id = resumo.region_id.astype(int)
    acps = pd.read_csv('../ACPs_MUN_CODES.csv',
                       sep=';')
    acps.columns=['acps', 'region_id']
    resumo = pd.merge(resumo, acps, how='outer', on=['region_id'])
    res2 = resumo.groupby(by=['region_id', 'month']).agg('mean')
    res2 = res2.reset_index()
    res2.to_csv('resumo_mun_month.csv', sep=';', index=False)

    temp = resumo.groupby(['month']).agg('median').reset_index().drop(['region_id'], axis=1)
    temp.month = temp.month.astype(int)

    model_general = concatenating_columns(files, cols)
    model_general = model_general.reset_index()
    model_general.month = model_general.month.astype(int)
    model_general = model_general.drop(model_general.loc[:, ['model_qli_index', 'model_unemployment']], axis=1)
    model_general = pd.merge(model_general, temp, how='outer', on=['month'])
    general = pd.merge(real_general, model_general, how='outer', on='month')
    general.rename(columns={'ipca': 'real_inflation', 'consumo_k': 'real_fam_consumption'}, inplace=True)

    general.to_csv('general_median.csv', sep=';', index=False)


if __name__ == "__main__":

    os.chdir(r'C:\Users\r1702898\Documents\Modelagem\MeusModelos\Empirical_v4\ValidatingData')
    cleaning()
    # Load real data to compare
    real_data = load_real_data()
    # Files to examine
    # Assuming all results files are in a single directory
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = r'\\storage4\carga\MODELO DINAMICO DE SIMULACAO\Exits_python\JULY\acps__2017-10-31T16_49_53.970313'
    files_path = load_regional_files_path(path)

    real_general = read_real_general()
    files_general_path, cols_names_general = load_model_general(path)
    res = feeding_files(files_path, real_data)
    saving(res, real_general, files_general_path, cols_names_general)
