import pandas as pd

try:
    names = pd.read_csv('../input/names_and_codes_municipalities.csv', sep=';', header=0)
except FileNotFoundError:
    names = pd.read_csv('./input/names_and_codes_municipalities.csv', sep=';', header=0)


def mun_name(cod):
    print(names[names.loc[:, 'cod_mun'] == cod]['cod_name'].iloc[0])


if __name__ == "__main__":

    stats = ['months', 'price_index', 'gdp_index', 'gdp_growth', 'unemployment', 'average_workers', 'families_wealth',
             'families_savings', 'firms_wealth', 'firms_profit', 'gini_index', 'average_utility', 'inflation',
             'average_qli']
    regions = ['months', 'region.id', 'commuting', 'region.pop', 'region.gdp', 'regional_gini', 'regional_house_values',
               'regional_unemployment', 'qli_index', 'GDP_region_capita', 'total_treasure', 'treasure_consumption',
               'region.cumulative_treasure_property', 'treasure_labor', 'treasure_firm', 'treasure_transaction',
               'treasure_fpm']
    agents = ['months', 'region_id','gender', 'long', 'lat' 'agent.id', 'age', 'qualification', 'firm_id', 'family.id',
              'money', 'utility', 'distance']
    firms = ['months', 'firm.id', 'region_id', 'long', 'lat', 'total_balance', 'num_employees', 'total_quantity',
             'amount_produced', 'price', 'amount_sold', 'revenue', 'profit', 'wages_paid']
    houses = ['months', 'house.id','long', 'lat', 'size', 'price', 'family_id',  'region_id']
    families = ['months', 'family.id', 'house.price', 'region_id', 'savings', 'num_members', 'firm_strategy']

    mun_name(3106200)
