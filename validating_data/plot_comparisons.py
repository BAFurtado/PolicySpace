import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import ks_2samp
from sklearn.preprocessing import scale
from statsmodels.graphics.gofplots import qqplot_2samples as qq


def plot_qq(x, y):
    # Checking length
    if len(x) > len(y):
        x = x[:len(y)]
    else:
        y = y[:len(x)]
    return qq(x, y, line='45')


def plot_density_test_ks(files, cols_x, cols_y):
    sns.set()
    for i in range(len(cols_x)):
        for j in range(len(files)):
            try:
                plt.figure()
                x = scale(files[j][cols_x[i]][~files[j][cols_x[i]].isnull()])
                y = scale(files[j][cols_y[i]][~files[j][cols_y[i]].isnull()])
                sns.distplot(x, hist=False, label=cols_x[i])
                sns.distplot(y, hist=False, label=cols_y[i])
                plt.legend()
                k = ks_2samp(x, y)
                if j == 0:
                    l = 'general'
                    plt.title('{}: {}\n Teste Kolmogorov Smirnov. '
                              'P-valor: {:.4f}'.format(l.capitalize(), cols_x[i][5:].capitalize().replace('_', ' '), k[1]))
                    plt.savefig('outputs/general/' + cols_x[i][5:] + '_' + l)
                    fig = plot_qq(x, y)
                    plt.savefig('outputs/qq/general/' + cols_x[i][5:] + '_' + l)
                elif j == 1:
                    l = 'mun'
                    plt.title('{}: {}\n Teste Kolmogorov Smirnov. '
                              'P-valor: {:.4f}'.format(l.capitalize(), cols_x[i][5:].capitalize().replace('_', ' '), k[1]))
                    plt.savefig('outputs/mun/' + cols_x[i][5:] + '_' + l)
                    fig = plot_qq(x, y)
                    plt.savefig('outputs/qq/mun/' + cols_x[i][5:] + '_' + l)
                else:
                    l = 'acp'
                    plt.title('{}: {}\n Teste Kolmogorov Smirnov. '
                              'P-valor: {:.4f}'.format(l.capitalize(), cols_x[i][5:].capitalize().replace('_', ' '), k[1]))
                    plt.savefig('outputs/acp/' + cols_x[i][5:] + '_' + l)
                    fig = plot_qq(x, y)
                    plt.savefig('outputs/qq/acp/' + cols_x[i][5:] + '_' + l)

                print("{} KS: P.value median cols: {} x {} {:.05f}".format(l, cols_x[i], cols_y[i], k[1]))
            except KeyError:
                 print('Não rolou: {}_{}'.format(cols_x[i][5:], j))


def plot_general_real_model(file, x, y):
    for i in range(len(x)):
        for j in range(len(file)):
            try:
                if j == 0:
                    l = 'general'
                    a = scale(file[j][x[i]][~file[j][x[i]].isnull()])
                    b = scale(file[j][y[i]][~file[j][y[i]].isnull()])

                    fig, ax = plt.subplots()
                    sns.set()

                    plt.plot(file[j]['month'][:len(a)], a)
                    plt.plot(file[j]['month'][:len(b)], b)
                    plt.savefig('outputs/' + l + '/series/' + x[i][5:])

                else:
                    l = 'mun'
                    group = file[j].groupby('month').agg('mean')
                    plt.plot(group.index, group[x[i]][~group[x[i]].isnull()])
                    plt.plot(group.index, group[y[i]][~group[y[i]].isnull()])
                    plt.savefig('outputs/' + l + '/series/' + x[i][5:])
            except:
                print("No column available or NaN values in this file")


if __name__ == "__main__":
    # Importing files to plot
    general = pd.read_csv('general_median.csv', sep=';')
    mun = pd.read_csv('resumo_mun_month.csv', sep=';')
    acp = pd.read_csv('summary_results_acp.csv', sep=';')

    # Reordering columns
    real = ['real_inflation',
            'real_gdp_region',
              'real_fam_consumption',
              'real_fpm',
              'real_gdp_region',
              'real_pop',
              'real_prop_fpm_gdp',
              'real_prop_fpm_total',
              'real_prop_property_total',
              'real_prop_transaction_total',
              'real_prop_property_gdp',
              'real_prop_transaction_gdp',
              'real_prop_treasure_gdp',
              'real_property',
              'real_qli_index',
              'real_transaction',
              'real_treasure',
              'real_unemployment']

    model = ['model_inflation',
             'model_gdp_region',
              'model_fam_consumption',
              'model_fpm',
              'model_gdp_region',
              'model_pop',
              'model_prop_fpm_gdp',
              'model_prop_fpm_total',
              'model_prop_property_total',
              'model_prop_transaction_total',
              'model_prop_property_gdp',
              'model_prop_transaction_gdp',
              'model_prop_treasure_gdp',
              'model_property',
              'model_qli_index',
              'model_transaction',
              'model_treasure',
              'model_unemployment']

    alt = [general, mun, acp]
    plot_density_test_ks(alt, real, model)
    # plot_general_real_model([general, mun], real, model)
