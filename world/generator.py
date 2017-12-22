"""
This is the module that uses input data to generate the artificial entities (instances)
used in the model. First, regions - the actual municipalities - are created using
shapefile input of real limits and real urban/rural areas.
Then, Agents are created and bundled into families, given population measures.
Then, houses and firms are created and families are allocated to their first houses.
"""
import conf
import shapely
import logging
import pandas as pd
from .shapes import prepare_shapes
from .population import pop_age_data
from agents import Agent, Family, Firm, Region, House

logger = logging.getLogger('generator')

# Necessary input Data
prop_urban = pd.read_csv('input/prop_urban_rural_2000.csv', sep=';', header=0,
                         decimal=',').apply(pd.to_numeric, errors='coerce')
num_emp = pd.read_csv('input/firms_data_by_municipalities.csv', sep=';', header=0,
                      decimal=',').apply(pd.to_numeric, errors='coerce')
idhm = pd.read_csv('input/idhm_1991_2010.txt', sep=',', header=0,
                   decimal='.').apply(pd.to_numeric, errors='coerce')
idhm = idhm.loc[idhm['year'] == conf.RUN['YEAR_TO_START']]
quali = pd.read_csv('input/qualification_2000.csv', sep=';', header=0,
                    decimal=',').apply(pd.to_numeric, errors='coerce')
quali = quali.drop('Unnamed: 0', 1)
quali.set_index('cod_mun', inplace=True)
quali_sum = quali.cumsum(axis=1)


class Generator:
    def __init__(self, sim):
        self.sim = sim
        self.seed = sim.seed
        self.urban, self.shapes = prepare_shapes(sim.geo)

    def create_regions(self):
        """Create regions"""
        regions = {}
        for item in self.shapes:
            r = Region(item)
            r.index = idhm[idhm['cod_mun'] == int(r.id)]['idhm'].iloc[0]
            regions[r.id] = r
        return regions

    def create_all(self, pops, regions):
        """Based on regions and population data,
        create agents, families, houses, and firms"""
        agent_id = 0
        house_id = 0
        family_id = 0
        firm_id = 0
        my_agents = {}
        my_families = {}
        my_houses = {}
        my_firms = {}
        for region_id, region in regions.items():
            logger.info('Generating region {}'.format(region_id))
            num_houses = 0
            regional_agents = {}

            pop_cols = list(list(pops.values())[0].columns)
            if not self.sim.PARAMS['SIMPLIFY_POP_EVOLUTION']:
                list_of_possible_ages = pop_cols[1:]
            else:
                list_of_possible_ages = [0] + pop_cols[1:]

            loop_age_control = list(list_of_possible_ages)
            loop_age_control.pop(0)

            for age in loop_age_control:
                for gender in ['male', 'female']:
                    cod_mun = region.id
                    pop = pop_age_data(pops[gender], cod_mun, age, self.sim.PARAMS['PERCENTAGE_ACTUAL_POP'])
                    for individual in range(pop):
                        # Qualification
                        # To see a histogram check test:
                        qualification = self.qual(cod_mun)
                        r_age = self.seed.randint(list_of_possible_ages[(list_of_possible_ages.index(age, ) - 1)] + 1,
                                                    age)
                        money = self.seed.randrange(50, 100)
                        month = self.seed.randrange(1, 13, 1)
                        a = Agent(agent_id, gender, r_age, qualification, money, month)
                        regional_agents[agent_id] = a
                        agent_id += 1
                        num_houses += 1

            for agent in regional_agents.keys():
                my_agents[agent] = regional_agents[agent]

            num_families = int(num_houses / self.sim.PARAMS['MEMBERS_PER_FAMILY'])
            num_houses = int(num_houses / self.sim.PARAMS['MEMBERS_PER_FAMILY'] * (1 + self.sim.PARAMS['HOUSE_VACANCY']))
            num_firms = int(num_emp[num_emp['cod_mun'] == int(region.id)]['num_est'].iloc[0] *
                            self.sim.PARAMS['PERCENTAGE_ACTUAL_POP'])

            regional_families = (self.create_family(num_families, family_id))
            family_id += num_families

            regional_houses = self.create_household(num_houses, region, house_id)
            house_id += num_houses

            regional_firms = self.create_firm(num_firms, region, firm_id)
            firm_id += num_firms

            for family in regional_families.keys():
                my_families[family] = regional_families[family]

            for house in regional_houses.keys():
                my_houses[house] = regional_houses[house]

            for firm in regional_firms.keys():
                my_firms[firm] = regional_firms[firm]

            regional_agents, regional_families = self.allocate_to_family(regional_agents, regional_families)
            regional_families = self.allocate_to_households(regional_families, regional_houses)

            # Set ownership of remaining houses for random families
            for house in regional_houses.keys():
                if regional_houses[house].owner_id is None:
                    family = self.seed.choice(list(regional_families.keys()))
                    regional_houses[house].owner_id = regional_families[family].id
        return my_agents, my_houses, my_families, my_firms

    def create_family(self, num_families, family_id):
        community = {}
        for _ in range(num_families):
            community[family_id] = Family(family_id)
            family_id += 1
        return community

    def allocate_to_family(self, agents, families):
        """Allocate agents to families"""
        agents = list(agents.values())
        self.seed.shuffle(agents)
        fams = list(families.values())
        for agent in agents:
            family = self.seed.choice(fams)
            if not agent.belongs_to_family:
                family.add_agent(agent)
        return agents, families

    # Address within the region
    # Additional details so that address fall in urban areas, given percentage
    def get_random_point_in_polygon(self, region, urban=True):
        while True:
            lat = self.seed.uniform(region.address_envelope[0],
                            region.address_envelope[1])
            lng = self.seed.uniform(region.address_envelope[2],
                            region.address_envelope[3])
            address = shapely.geometry.Point(lat,lng)
            if urban:
                item = self.urban[region.id]
                if item.contains(address):
                    return address
            elif region.addresses.contains(address):
                return address

    def create_household(self, num_houses, region, house_id):
        """Create houses for a region"""
        neighborhood = {}
        probability_urban = prop_urban[prop_urban['cod_mun'] == int(region.id)]['prop_urb'].iloc[0]
        for _ in range(num_houses):
            urban = self.seed.random() < probability_urban
            address = self.get_random_point_in_polygon(region, urban=urban)
            size = self.seed.randrange(20, 120)
            # Price is given by 4 quality levels
            quality = self.seed.choice([1, 2, 3, 4])
            price = size * quality * region.index
            h = House(house_id, address, size, price, region.id, quality, urban)
            neighborhood[house_id] = h
            house_id += 1
        return neighborhood

    def allocate_to_households(self, families, households):
        """Allocate houses to families"""
        unclaimed = list(households)
        self.seed.shuffle(unclaimed)
        house_id = unclaimed.pop(0)
        for family in families.values():
            if family.members:
                house = households[house_id]
                if not house.is_occupied:
                    family.move_in(house)
                    house.owner_id = family.id
                    house_id = unclaimed.pop(0)
        return families

    def create_firm(self, num_firms, region, firm_id):
        sector = {}
        for _ in range(num_firms):
            address = self.get_random_point_in_polygon(region)
            total_balance = self.seed.betavariate(1.5, 10) * 100000
            f = Firm(firm_id, address, total_balance, region.id)
            sector[f.id] = f
            firm_id += 1
        return sector

    def qual(self, cod):
        sel = quali_sum > self.seed.random()
        idx = sel.idxmax(1)
        loc = idx.loc[int(cod)]
        return int(loc)
