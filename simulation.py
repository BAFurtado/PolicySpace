import os
import conf
import json
import pickle
import random
import markets
import analysis
import pandas as pd
from collections import defaultdict
from world import Generator, demographics, clock, population
from world.geography import Geography, STATES_CODES, state_string
from world.funds import Funds


class Simulation:
    def __init__(self, params, output_path):
        self.PARAMS = params
        self.geo = Geography(params)
        self.funds = Funds(self)
        self.clock = clock.Clock()
        self.output = analysis.Output(self, output_path)
        self.stats = analysis.Statistics()
        self.logger = analysis.Logger(hex(id(self))[-5:])
        self.timer = analysis.Timer()
        self.seed = random if conf.RUN['KEEP_RANDOM_SEED'] else random.Random(0)

        # Read necessary files
        self.m_men, self.m_women, self.f = {}, {}, {}
        for state in self.geo.states_on_process:
            self.m_men[state] = pd.read_csv('input/mortality/mortality_men_%s.csv' % state, sep=';', header=0, decimal='.').groupby('age')
            self.m_women[state] = pd.read_csv('input/mortality/mortality_women_%s.csv' % state, sep=';', header=0, decimal='.').groupby('age')
            self.f[state] = pd.read_csv('input/fertility/fertility_%s.csv' % state, sep=';', header=0, decimal='.').groupby('age')

    def generate(self):
        """Spawn or load regions, agents, houses, families, and firms"""
        generator = Generator(self)
        save_file = '{}.agents'.format(self.output.save_name)
        if not os.path.isfile(save_file) or conf.RUN['FORCE_NEW_POPULATION']:
            self.logger.info('Creating new agents')
            regions = generator.create_regions()
            agents, houses, families, firms = generator.create_all(self.pops, regions)
            agents = {a: agents[a] for a in agents.keys() if agents[a].address is not None}
            with open(save_file, 'wb') as f:
                pickle.dump([agents, houses, families, firms, regions], f)
        else:
            self.logger.info('Loading existing agents')
            with open(save_file, 'rb') as f:
                 agents, houses, families, firms, regions = pickle.load(f)
        return regions, agents, houses, families, firms

    def run(self):
        """Runs the simulation"""
        self.logger.info('Starting run.')
        self.logger.info('Output: {}'.format(self.output.path))
        self.logger.info('Params: {}'.format(json.dumps(self.PARAMS)))

        timer = analysis.Timer()
        timer.start()

        self.labor_market = markets.LaborMarket(self.seed)
        self.pops, self.total_pop = population.load_pops(self.geo.mun_codes, self.PARAMS)
        self.regions, self.agents, self.houses, self.families, self.firms = self.generate()
        self.logger.info('Initializing...')
        self.initialize()

        self.logger.info('Running...')
        while self.clock.days < conf.RUN['TOTAL_DAYS']:
            self.daily()
            if self.clock.new_month:
                self.monthly()
            if self.clock.new_quarter:
                self.quarterly()
            if self.clock.new_year:
                self.yearly()
            self.clock.days += 1

        if conf.RUN['PRINT_FINAL_STATISTICS_ABOUT_AGENTS']:
            self.logger.log_outcomes(self)

        self.logger.info('Simulation completed.')
        self.logger.info('Run took {:.2f}s'.format(timer.elapsed()))

    def initialize(self):
        """Initiating simulation"""
        self.grave = []

        # Beginning of simulation, generate a product
        for firm in self.firms.values():
            firm.create_product()

        # First jobs allocated
        # Create an existing job market
        # Leave only 5% residual unemployment as of simulation starts
        self.labor_market.look_for_jobs(self.agents)
        total = actual = self.labor_market.num_candidates
        actual_unemployment = self.stats.global_unemployment_rate / 100
        # Simple average of 6 Metropolitan regions Brazil January 2000
        while actual / total > .086:
            self.labor_market.hire_fire(self.firms, self.PARAMS['LABOR_MARKET'])
            self.labor_market.assign_post(actual_unemployment, self.PARAMS)
            self.labor_market.look_for_jobs(self.agents)
            actual = self.labor_market.num_candidates
        self.labor_market.reset()

        # Update initial pop
        for region in self.regions.values():
            region.update_pop(self.families)

    def daily(self):
        pass

    def monthly(self):
        # Save month for statistics purpose
        present_month = self.clock.months
        present_year = self.clock.year
        current_unemployment = self.stats.global_unemployment_rate / 100

        # Call demographics

        # Insert days activities here ################################################################################
        # Regular production. Everyday activities

        self.timer.start()
        for firm in self.firms.values():
            firm.update_product_quantity(self.PARAMS['ALPHA'], self.PARAMS['PRODUCTION_MAGNITUDE'])

        # Update agent life cycles
        for state in self.geo.states_on_process:
            mortality_men = self.m_men[state]
            mortality_women = self.m_women[state]
            fertility = self.f[state]

            state_str = state_string(state, STATES_CODES)

            birthdays = defaultdict(list)
            for agent in self.agents.values():
                if (present_month % 12 + 1) == agent.month \
                    and agent.region_id[:2] == state_str:
                    birthdays[agent.age].append(agent)

            demographics.check_demographics(self, birthdays, present_year, mortality_men, mortality_women, fertility)

        self.logger.log_time('DEMOGRAPHICS', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # Firms initialization
        self.timer.start()
        for firm in self.firms.values():
            firm.actual_month = present_month
            firm.amount_sold = 0

        self.logger.log_time('FIRMS INITIALIZATION', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # FAMILIES CONSUMPTION
        # Equalize money within family members
        # Tax firms when doing sales
        self.timer.start()
        markets.goods.consume(self)

        self.logger.log_time('CONSUME FAMILY', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # FIRMS
        # Update profits
        # Check if necessary to update prices
        self.timer.start()
        for firm in self.firms.values():
            firm.calculate_revenue()
            # Tax firms before profits: (revenue - salaries paid)
            firm.pay_taxes(self.regions, current_unemployment, self.PARAMS['TAX_CONSUMPTION'], self.PARAMS['TAX_FIRM'])
            firm.calculate_profit()
            # Tax workers when paying salaries
            firm.make_payment(self.regions, current_unemployment,
                              self.PARAMS['ALPHA'],
                              self.PARAMS['TAX_LABOR'],
                              self.PARAMS['TAX_CONSUMPTION'],
                              self.PARAMS['WAGE_IGNORE_UNEMPLOYMENT'])
            firm.update_prices(self.PARAMS['STICKY_PRICES'], self.PARAMS['MARKUP'], self.seed)

        self.logger.log_time('FIRMS PROCESS', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # Initiating Labor Market
        # AGENTS
        self.timer.start()
        self.labor_market.look_for_jobs(self.agents)
        self.logger.log_time('PEOPLE LOOKING JOBS', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # FIRMS
        # Check if new employee needed (functions below)
        # Check if firing is necessary
        self.timer.start()
        self.labor_market.hire_fire(self.firms, self.PARAMS['LABOR_MARKET'])
        self.logger.log_time('HIRE FIRE', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # Job Matching
        self.timer.start()
        self.labor_market.assign_post(current_unemployment, self.PARAMS)
        self.logger.log_time('JOB MATCH', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # Initiating Real Estate Market
        # Tax transaction taxes (ITBI) when selling house
        # Property tax (IPTU) collected. One twelfth per month
        self.timer.start()
        markets.housing.allocate_houses(self)
        for house in self.houses.values():
            house.pay_property_tax(self)

        self.logger.log_time('HOUSE MARKET', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # Using all collected taxes to improve public services
        self.timer.start()
        self.funds.invest_taxes(self.geo.states_on_process, present_year)
        self.logger.log_time('TREASURE', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        # Pass monthly information to be stored in Statistics
        self.timer.start()
        self.output.save_stats_report(self)

        # Getting regional GDP
        self.output.save_regional_report(self)

        if conf.RUN['SAVE_AGENTS_DATA_MONTHLY']:
            self.output.save_data(self)

        self.logger.log_time('SAVING DATA', self.timer, self.clock.months)
        self.output.times.append(self.timer.elapsed())

        self.logger.info('Month: {}'.format(self.clock.months))

    def quarterly(self):
        if conf.RUN['SAVE_AGENTS_DATA_QUARTERLY']:
            self.output.save_data(self)
        self.logger.info('Quarter: {}'.format(self.clock.quarters))

    def yearly(self):
        if conf.RUN['SAVE_AGENTS_DATA_ANNUALLY']:
            self.output.save_data(self)
        self.logger.info('Years: {}'.format(self.clock.years))
