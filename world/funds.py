import pandas as pd
from .geography import STATES_CODES, state_string


class Funds:
    def __init__(self, sim):
        self.sim = sim
        if sim.PARAMS['FPM_DISTRIBUTION']:
            self.fpm = {
                state: pd.read_csv('input/fpm/%s.csv' % state, sep=',', header=0, decimal='.', encoding='latin1')
                for state in self.sim.geo.states_on_process}

    def _distribute_fpm(self, regions, value, states_numbers, year, pop_t):
        """Calculate proportion of FPM per region, in relation to the total of all regions.
        Value is the total value of FPM to distribute"""
        if float(year) > 2016:
            year = str(2016)

        # Dictionary that keeps actual FPM received to be used as a proportion parameter
        # to simulated FPM to be distributed
        fpm_region = {}
        for i, state in enumerate(self.sim.geo.states_on_process):
            for id, region in regions.items():
                if region.id[:2] == states_numbers[i]:
                    fpm_region[id] = self.fpm[state][(self.fpm[state].ano == float(year)) &
                                    (self.fpm[state].cod == float(region.id))].fpm.iloc[0]

        for id, region in regions.items():
            regional_fpm = fpm_region[id] / sum(fpm_region.values()) * value
            # Saving FPM actually invested in each region
            region.cumulative_treasure['fpm'] += regional_fpm
            # Actually investing the FPM
            region.update_index(regional_fpm * self.sim.PARAMS['TREASURE_INTO_SERVICES'] / pop_t[id])

    def invest_taxes(self, states_on_process, year):
        # Collect and update pop_t-1 and pop_t
        regions = self.sim.regions
        families = self.sim.families
        pop_t_minus_1 = dict()
        pop_t = dict()
        for id, region in regions.items():
            pop_t_minus_1[id] = region.pop
            region.update_pop(families)
            pop_t[id] = region.pop
            # Update proportion of index coming from population variation
            region.update_index_pop(pop_t_minus_1[id]/pop_t[id])

        if self.sim.PARAMS['ALTERNATIVE0'] and self.sim.PARAMS['FPM_DISTRIBUTION']:
            # Situation as it is presently, considering taxes rules
            # Distributing considering FPM, then locally and the rest equally (Union/States)
            self.distribute_fpm(regions, pop_t, states_on_process, year)
        elif self.sim.PARAMS['ALTERNATIVE0']:
            # Situation as it is presently, but not considering taxes rules
            # Distributing everything locally
            self.locally(regions, pop_t, True)
        elif self.sim.PARAMS['FPM_DISTRIBUTION']:
            # Distribute part as FPM and rest equally
            self.distribute_fpm(regions, pop_t, states_on_process, year, False)
        else:
            # Distributing everything equally
            self.equally(regions, pop_t)

    def distribute_fpm(self, regions, pop_t, states_on_process, year, loc=True):
        """Deduce values of taxes from regions treasures.
        Deduce first FPM and EQUALLY is what is left"""
        v_fpm, v_equally = 0, 0
        for region in regions.values():
            v_fpm += region.collect_fpm(self.sim.PARAMS['TAXES_STRUCTURE'])
            v_equally += region.collect_equally_portion(self.sim.PARAMS['TAXES_STRUCTURE'])
        assert v_fpm >= 0, print(v_fpm)
        assert v_equally >= 0

        # Distribute FPM
        if v_fpm > 0:
            states_numbers = [state_string(state, STATES_CODES) for state in states_on_process]
            self._distribute_fpm(regions, v_fpm, states_numbers, year, pop_t)

        # Distribute equally, portion that comes from consumption, labor and firm (replicating Union and States)
        self.equally(regions, pop_t, v_equally, clean=False)

        # Distribute locally, just property, transaction and part of consumption (the residual treasure)
        if loc:
            self.locally(regions, pop_t, True)
        else:
            self.equally(regions, pop_t, clean=True)

    def locally(self, regions, pop_t, clean):
        """Distribute taxes according to origin"""
        for region in regions.keys():
            regions[region].update_index(regions[region].total_treasure * self.sim.PARAMS['TREASURE_INTO_SERVICES'] / pop_t[region],
                                        clean)

    def equally(self, regions, pop_t, total_treasure=None, clean=False):
        "Distribute taxes equally"""
        if total_treasure is None:
            total_treasure = 0
            clean = True
            for region in regions.values():
                total_treasure += region.total_treasure

        for region in regions.values():
            region.update_index((total_treasure * self.sim.PARAMS['TREASURE_INTO_SERVICES'] / sum(pop_t.values())), clean)
