import json
from shapely.geometry import shape


class Region():
    """Collects taxes and applies to ameliorate quality of life"""

    def __init__(self, region, index=1, gdp=0, pop=0, total_commute=0):
        # A region is an OSGEO object that contains Fields and Geometry
        self.address_envelope = region.geometry().GetEnvelope()
        self.addresses = region.geometry()
        # Make sure FIELD 2 is Name
        self.name = region.GetFieldAsString(2)
        # Make sure FIELD 1 is IBGE CODE
        self.id = region.GetField(1)
        self.addresses = shape(json.loads(self.addresses.ExportToJson()))
        self.index = index
        self.gdp = gdp
        self.pop = pop
        self.total_commute = total_commute
        self.cumulative_treasure = {
            'consumption': 0,
            'property': 0,
            'labor': 0,
            'firm': 0,
            'transaction': 0,
            'fpm': 0
        }
        self.treasure = {
            'consumption': 0,
            'property': 0,
            'labor': 0,
            'firm': 0,
            'transaction': 0
        }

    @property
    def total_treasure(self):
        return sum(self.treasure.values())

    def collect_taxes(self, amount, key):
        self.treasure[key] += amount

    @property
    def cumulative_total_treasure(self):
        """Total treasure does not include FPM, just the category taxes.
        FPM is a transfer generated from 'labor' and 'firm'"""
        return sum(self.cumulative_treasure.values()) - self.cumulative_treasure['fpm']

    def update_pop(self, families):
        pop = 0
        for family in families.values():
            if family.region_id == self.id:
                pop += len(family.members)
        self.pop = pop

    def save_and_clear_treasure(self):
        for key in self.treasure.keys():
            self.cumulative_treasure[key] += self.treasure[key]
            self.treasure[key] = 0

    def collect_fpm(self, taxes):
        value1 = self.treasure['labor'] * taxes['labor']['fpm']
        value2 = self.treasure['firm'] * taxes['firm']['fpm']
        self.treasure['labor'] -= value1
        self.treasure['firm'] -= value2
        self.cumulative_treasure['labor'] += value1
        self.cumulative_treasure['firm'] += value2
        return value1 + value2

    def collect_equally_portion(self, taxes):
        # As the fpm percentage is grabbed first, the full amount left is equivalent to taxes['labor'/'firm']['equally']
        value1 = self.treasure['consumption'] * taxes['consumption']['equally']
        value2 = self.treasure['labor']
        value3 = self.treasure['firm']
        self.treasure['consumption'] -= value1
        self.treasure['labor'] -= value2
        self.treasure['firm'] -= value3
        self.cumulative_treasure['consumption'] += value1
        self.cumulative_treasure['labor'] += value2
        self.cumulative_treasure['firm'] += value3
        return value1 + value2 + value3

    def update_index_pop(self, proportion_pop):
        """First term of QLI update, relative to change in population within its territory"""
        self.index *= proportion_pop

    def update_index(self, value, clean=False):
        """Index is updated per capita for current population"""
        self.index += value
        if clean:
            self.save_and_clear_treasure()

    def __repr__(self):
        return '%s \n QLI: %.2f, \t GDP: %.2f, \t Pop: %s, Commute: %.2f' % (self.name, self.index, self.gdp,
                                                                             self.pop, self.total_commute)
