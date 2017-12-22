import sys
import os

import matplotlib.pyplot as plt
import pandas as pd

from itertools import combinations


from bokeh.charts import output_file, Chord
from bokeh.io import show
from bokeh.sampledata.les_mis import data


pd.options.display.float_format = '{:,.2f}'.format

''' Saving code to plot families house prices changes '''


def organize(f):
    f.columns=['months', 'id', 'long', 'lat', 'size', 'house_value', 'family_id', 'region_id']
    return f


def plot(f):
    f = organize(f)
    f = f[f['family_id'] != 'None']
    g = (f.sort_values('months').groupby('family_id').filter(lambda g: g.house_value.iat[-1] != g.house_value.iat[0]))
    fplot = g.pivot(index='months', columns='family_id', values='house_value')
    fplot.plot()
    plt.show()


def basics(f):
    g = organize(f)
    non = g[g.family_id != 'None']
    vacant = (1 - len(non)/len(g)) * 100
    #vacant_region = g[g['family_id'] == 'None'].groupby('region_id').id.count() / \
                    # g.groupby('region_id').id.count() * 100
    m239 = g[g.months==0].house_value.mean()
    perc = (g[g.months==239].house_value.mean() - m239) / m239 * 100

    move = (non.sort_values('months').groupby('family_id').filter(lambda h: h.house_value.iat[-1] !=
                                                                            h.house_value.iat[0]))
    up = (non.sort_values('months').groupby('family_id').filter(lambda h: h.house_value.iat[-1] >
                                                                          h.house_value.iat[0]))
    down = (non.sort_values('months').groupby('family_id').filter(lambda h: h.house_value.iat[-1] <
                                                                            h.house_value.iat[0]))

    num_families = len(set(move.family_id))

    p = 'Families which moved upwards/downwards weighed by the number of families which moved from a given municipality.'
    up_down = pd.DataFrame()
    up_down['up'] = up[up.months==239].groupby('region_id').family_id.count() / \
              move[move.months==0].groupby('region_id').family_id.count()
    up_down['down'] = down[down.months==239].groupby('region_id').family_id.count() / \
              move[move.months==0].groupby('region_id').family_id.count()

    # stack bar plot
    up_down.sort_values('up').plot(kind='barh', stacked=True)
    #plt.show()

    print('Vacant houses: {:.2f}%'.format(vacant))
    # print('Vacant houses by municipalities: {}%'.format(vacant_region.to_string()))
    print('Mean house values: full base ${:.2f}'.format(g.house_value.mean()))
    print('Mean house values: occupied ${:.2f}'.format(non.house_value.mean()))
    print('Mean house values: vacant base ${:.2f}'.format(g[g.family_id=='None'].house_value.mean()))
    print('Percentage of increase house prices for given period: {:.2f} %'.format(perc))
    print('Number of families that have moved: {:.0f}. '
          'Percentage of total families {:.2f} %'.format(num_families, num_families / len(set(g.family_id)) * 100))
    print('Upwards {:.2f}% and Downwards {:.2f} %'.format(float(len(set(up.family_id)) / num_families) * 100,
                                                         float(len(set(down.family_id)) / num_families) * 100))


def plot_chord(df, names):

    # Cleaning up received DataFrame
    df = organize(df)
    df = df[['family_id', 'region_id']]
    tf = df.drop_duplicates(keep='first')
    tl = df.drop_duplicates(keep='last')
    df = pd.concat([tf, tl])

    # Generating nodes and links
    cnxns = []
    for k, g in df.groupby('family_id'):
        [cnxns.extend((n1, n2, len(g)) for n1, n2 in combinations(g['region_id'], 2))]
    df = pd.DataFrame(cnxns, columns=['region1', 'region2', 'total'])
    df = df.groupby(['region1', 'region2']).agg('sum')
    df = df.reset_index()

    # Chord won't work with duplicated places
    df = df[df.region1 != df.region2]

    # Using only most relevant links
    df = df[df.total > 100]

    # Associating names
    df = pd.merge(df, names, how='inner', left_on='region1', right_on='cod_mun')
    df = df[['region2', 'total', 'cod_name']]
    df = pd.merge(df, names, how='inner', left_on='region2', right_on='cod_mun')
    df = df[['cod_name_x', 'cod_name_y', 'total']]

    # Making and saving and showing Chord
    chord = Chord(df, source='cod_name_x', target='cod_name_y', value='total')
    output_file('chord.html', mode='inline')
    show(chord)

if __name__ == "__main__":

    if len(sys.argv) > 1:
        file = pd.read_csv(sys.argv[1], sep=';', header=None)
    else:
        file = pd.read_csv(r'\\storage4\carga\MODELO DINAMICO DE SIMULACAO\Exits_python\JULY\sensitivity\pct_check\sensitivity__2017-11-10T12_58_22.339654_pct_check_new_location_BSB_newvalues\PERCENTAGE_CHECK_NEW_LOCATION=0.02\0\temp_houses.csv',
                           sep=';', header=None)
    try:
        mun_names = pd.read_csv('./input/names_and_codes_municipalities.csv', sep=';', header=0)
    except FileNotFoundError:
        mun_names = pd.read_csv('../input/names_and_codes_municipalities.csv', sep=';', header=0)
    basics(file)
    #plot(file)
    #plot_chord(file, mun_names)