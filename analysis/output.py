import os
import conf
from collections import defaultdict

AGENTS_PATH = 'StoragedAgents'
if not os.path.exists(AGENTS_PATH):
    os.mkdir(AGENTS_PATH)

# These are the params which specifically
# affect agent generation.
# We check when these change so
# we know to re-generate the agent population.
GENERATOR_PARAMS = [
    'MEMBERS_PER_FAMILY',
    'HOUSE_VACANCY',
    'SIMPLIFY_POP_EVOLUTION',
    'PERCENTAGE_ACTUAL_POP'
]


class Output:
    """Manages simulation outputs"""

    def __init__(self, sim, output_path):
        files = ['stats', 'regional', 'time', 'firms',
                 'houses', 'agents', 'families', 'grave']

        self.sim = sim
        self.times = []
        self.path = output_path

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        for p in files:
            path = os.path.join(self.path, 'temp_{}.csv'.format(p))
            setattr(self, '{}_path'.format(p), path)

            # reset files for each run
            if os.path.exists(path):
                os.remove(path)

        self.save_name = '{}/{}_states_{}_acps_{}'.format(
            AGENTS_PATH,
            '_'.join([str(self.sim.PARAMS[name]) for name in GENERATOR_PARAMS]),
            '_'.join(sim.geo.states_on_process),
            '_'.join(sim.geo.processing_acps_codes)
        )

    def save_stats_report(self, sim):
        price_index, inflation = sim.stats.update_price(sim.firms)
        gdp_index, gdp_growth = sim.stats.sum_region_gdp(sim.firms, sim.regions)
        unemployment = sim.stats.update_unemployment(sim.agents.values(), True)
        average_workers = sim.stats.calculate_average_workers(sim.firms)
        families_wealth, families_savings = sim.stats.calculate_families_wealth(sim.families)
        firms_wealth = sim.stats.calculate_firms_wealth(sim.firms)
        firms_profit = sim.stats.calculate_firms_profit(sim.firms)
        gini_index = sim.stats.calculate_GINI(sim.families)
        average_utility = sim.stats.calculate_utility(sim.families)
        average_qli = sim.stats.average_qli(sim.regions)

        # TODO: include names of columns os csv files. It can't interfere with plotting
        report = '{};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.3f};{:.4f};{:.4f}\n'.format(
                    sim.clock.months, price_index, gdp_index,
                    gdp_growth, unemployment, average_workers,
                    families_wealth, families_savings,
                    firms_wealth, firms_profit, gini_index,
                    average_utility, inflation, average_qli)

        with open(self.stats_path, 'a') as f:
            f.write(report)

    def save_regional_report(self, sim):
        reports = []
        agents_by_region = defaultdict(list)
        families_by_region = defaultdict(list)
        for agent in sim.agents.values():
            agents_by_region[agent.region_id].append(agent)
        for family in sim.families.values():
            families_by_region[family.region_id].append(family)
        for region in sim.regions.values():
            regional_agents = agents_by_region[region.id]
            regional_families = families_by_region[region.id]
            GDP_region_capita = sim.stats.update_GDP_capita(sim.firms, region)
            commuting = sim.stats.update_commuting(regional_families)
            regional_gini = sim.stats.calculate_regional_GINI(regional_families)
            regional_house_values = sim.stats.calculate_avg_regional_house_price(regional_families)
            regional_unemployment = sim.stats.update_unemployment(regional_agents)
            region.total_commute = commuting

            reports.append('%s;%s;%.3f;%d;%.3f;%.4f;%.3f;%.4f;%.5f;%.3f;%.5f;%.6f;%.6f;%.6f;%.6f;%.6f;%.6f'
                                % (sim.clock.months, region.id, commuting, region.pop, region.gdp,
                                    regional_gini, regional_house_values,
                                   regional_unemployment, region.index, GDP_region_capita,
                                    region.cumulative_total_treasure,
                                    region.cumulative_treasure['consumption'],
                                    region.cumulative_treasure['property'],
                                    region.cumulative_treasure['labor'],
                                    region.cumulative_treasure['firm'],
                                    region.cumulative_treasure['transaction'],
                                    region.cumulative_treasure['fpm']))

        with open(self.regional_path, 'a') as f:
            f.write('\n'+'\n'.join(reports))

    def save_data(self, sim):
        # firms data is necessary for plots,
        # so always save
        self.save_firms_data(sim)

        for type in conf.RUN['SAVE_DATA']:
            save_fn = getattr(self, 'save_{}_data'.format(type))
            save_fn(sim)

    def save_firms_data(self, sim):
        with open(self.firms_path, 'a') as f:
            [f.write('%d; %d; %s; %.3f; %.3f; %.3f; %d; %.3f; %.3f; %.3f ; %.3f; %.3f; %.3f; %.3f \n' %
                            (sim.clock.months, firm.id, firm.region_id, firm.address.x,
                            firm.address.y, firm.total_balance, firm.num_employees,
                            firm.total_quantity, firm.amount_produced, firm.inventory[0].price,
                            firm.amount_sold, firm.revenue, firm.profit,
                            firm.wages_paid))
            for firm in sim.firms.values()]

    def save_agents_data(self, sim):
        with open(self.agents_path, 'a') as f:
            [f.write('%d;%s;%s;%.3f;%.3f;%d;%d;%d;%s;%s;%.3f;%.3f;%s\n' % (sim.clock.months, agent.region_id,
                                                                           agent.gender, agent.address.x,
                                                                           agent.address.y, agent.id, agent.age,
                                                                           agent.qualification, agent.firm_id,
                                                                           agent.family.id, agent.money, agent.utility,
                                                                           agent.distance))
            for agent in sim.agents.values()]

    def save_grave_data(self, sim):
        with open(self.grave_path, 'a') as f:
            [f.write('%d;%s;%s;%s;%s;%d;%d;%d;%s;%s;%.3f;%.3f;%s\n' % (sim.clock.months, agent.region_id,
                                                                           agent.gender,
                                                                           agent.address.x if agent.address else None,
                                                                           agent.address.y if agent.address else None,
                                                                           agent.id, agent.age,
                                                                           agent.qualification, agent.firm_id,
                                                                           agent.family.id, agent.money, agent.utility,
                                                                           agent.distance))
            for agent in sim.grave]

    def save_house_data(self, sim):
        with open(self.houses_path, 'a') as f:
            [f.write('%d;%d;%f;%f;%.2f;%.2f;%s;%s\n' % (sim.clock.months,
                                                                house.id,
                                                                house.address.x,
                                                                house.address.y,
                                                                house.size,
                                                                house.price,
                                                                house.family_id,
                                                                house.region_id))
            for house in sim.houses.values()]

    def save_family_data(self, sim):
        with open(self.families_path, 'a') as f:
            [f.write('%s;%s;%s;%s;%.2f;%.2f;%s\n' % (sim.clock.months,
                                                            family.id,
                                                            family.house.price if family.house else 0,
                                                            family.region_id,
                                                            family.savings,
                                                            family.num_members,
                                                            family.firm_strategy))
            for family in sim.families.values()]
