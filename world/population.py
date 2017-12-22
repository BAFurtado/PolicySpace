import pandas as pd


def simplify_pops(pops, params):
    """Simplify population"""
    # Inserting the 0 on the new list of ages
    list_new_age_groups = [0] + params['LIST_NEW_AGE_GROUPS']

    pops_ = {}
    for gender, pop in pops.items():
        # excluding the first column (region ID)
        pop_edit = pop.iloc[:, pop.columns != 'cod_mun']

        # Transform the columns ID in integer values (to make easy to select the intervals and sum the pop. by region)
        list_of_ages = [int(x) for x in [int(t) for t in list(pop_edit.columns)]]
        # create the first aggregated age class
        temp = pop_edit.iloc[:, [int(t) <= list_new_age_groups[1] for t in list_of_ages]].sum(axis=1)
        # add the first column with the region ID
        pop_fmt = pd.concat([pop.iloc[:, pop.columns == 'cod_mun'], temp], axis=1)
        # excluding the processed columns in the previous age aggregation
        pop_edit = pop_edit.iloc[:, [int(i) > list_new_age_groups[1] for i in list_of_ages]]
        for i in range(1, len(list_new_age_groups) - 1):
            # creating the full new renaming ages list
            list_of_ages = [int(x) for x in [int(t) for t in list(pop_edit.columns)]]
            # selecting the new aggregated age class based on superior limit from list_new_age_groups, SUM by ROW
            temp = pop_edit.iloc[:, [int(t) <= list_new_age_groups[i + 1] for t in list_of_ages]].sum(axis=1)
            # joining to the previous processed age class
            pop_fmt = pd.concat([pop_fmt, temp], axis=1)
            # excluding the processed columns in the previous age aggregation
            pop_edit = pop_edit.iloc[:, [int(age) > list_new_age_groups[i + 1] for age in list_of_ages]]
        # changing the columns names
        pop_fmt.columns = ['cod_mun'] + list_new_age_groups[1:len(list_new_age_groups)]
        pops_[gender] = pop_fmt

    return pops_


def format_pops(pops):
    """Rename the columns names to be compatible as the pop simplification modification"""
    list_of_columns = ['cod_mun']+[int(x) for x in list(pops[0].columns)[1:len(list(pops[0].columns))]]
    for pop in pops.values():
        pop.columns = list_of_columns
    return pops


def pop_age_data(pop, code, age, percent_pop):
    """Select and return the proportion value of population
    for a given municipality, gender and age"""
    return int(round(pop[pop['cod_mun'] == int(code)][age].iloc[0] * percent_pop))


def load_pops(mun_codes, params):
    """Load populations for specified municipal codes."""
    pops = {}
    for name, gender in [('men', 'male'), ('women', 'female')]:
        pop = pd.read_csv('input/pop_{}.csv'.format(name), sep=';', header=0, decimal=',')
        pop = pop[pop['cod_mun'].isin(mun_codes)]
        pops[gender] = pop

    total_pop = sum(round(pop.iloc[:, pop.columns != 'cod_mun'].sum(axis=1).sum(0) * params['PERCENTAGE_ACTUAL_POP']) for pop in pops.values())
    if params['SIMPLIFY_POP_EVOLUTION']:
        pops = simplify_pops(pops, params)
    else:
        pops = format_pops(pops)
    return pops, total_pop
