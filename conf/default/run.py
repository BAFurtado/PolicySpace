# THE ROOT OUTPUT DATA LOCATION #######################################################################################
# Change your output directory as necessary

OUTPUT_PATH = '../output'
# OUTPUT_PATH = '/tmp/seal'

KEEP_RANDOM_SEED = True

# Descriptive stats to plot evolution of age and qualification by municipality
DESCRIPTIVE_STATS_CHOICE = False

# Visualization data through the simulation
DELETE_TESTS = True

# Logging
PRINT_STATISTICS_AND_RESULTS_DURING_PROCESS = False
PRINT_FINAL_STATISTICS_ABOUT_AGENTS = False
PRINT_TIME_CONTROL_IN_TIME_ITERATION = False

# Inform numbers in percentage of the period
TIME_TO_BE_ELIMINATED = 0.0

# Saving adjustments
SAVE_SPATIAL_PLOTS = True
SAVE_PLOTS_FIGURES = True
# Save Agents data and also PLOT regional plots
SAVE_AGENTS_DATA_MONTHLY = True
SAVE_AGENTS_DATA_QUARTERLY = False
SAVE_AGENTS_DATA_ANNUALLY = False

# What extra data (i.e. not necessary plotting) to save
# Can include: ['agents', 'grave', 'house', 'family']
# If None, set to empty list: []
SAVE_DATA = []

# Average all data (not just general data)
# across all runs
AVERAGE_ALL_DATA = False

# If plots should be generated separately
# for each simulation run or just aggregated
PLOT_EACH_RUN = True

# Maximum running time (restrained by official data) is 30 years, or 7560 days
TOTAL_DAYS = 2520

# Selecting the starting year to build the Agents, can be: 1991, 2000 or 2010
YEAR_TO_START = 2000

# Force generation of new population
FORCE_NEW_POPULATION = False
