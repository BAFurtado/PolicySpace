 # PolicySpace
 
 ### PolicySpace2 -- in-development -- now available at http://www.github.com/bafurtado/policyspace2

### Please, cite as: FURTADO, Bernardo Alves. PolicySpace: agent-based modeling. IPEA: Brasília, 2018.
Available here in English: http://www.ipea.gov.br/portal/index.php?option=com_content&view=article&id=33132&Itemid=433

Also available in Portuguese: 
http://www.ipea.gov.br/portal/index.php?option=com_content&view=article&id=32743&Itemid=433

This is an open agent-based model with three markets and a tax scheme that empirically simulates 46 Brazilian
metropolitan regions.

Developed by Bernardo Alves Furtado, funded by Institute of Applied Economic Research (IPEA).
The author acknowledges receiving a grant of productivity by National Council of Research (CNPq). Isaque Daniel Rocha Eberhardt and Francis Tseng were fundamental contributors (see below for participation details).

This work is licensed under GNU General Public License v3.0

### English summary 

PolicySpace: a modeling platform. (accepted to) https://arxiv.org/abs/1801.00259
CAPS 2018: Complexity and Policy Studies
UNCC - George Mason University - April 18 (but not presented).

### Repository of produced texts
https://www.researchgate.net/profile/Bernardo_Furtado

### Current collaborators
Bernardo Alves Furtado, Francis Tseng

#### Previous collaborators
Bernardo Alves Furtado, since beginning:(conception, design, coding - agents, markets, timeframe, general)
Isaque Daniel Rocha Eberhardt, 16 months:(design, coding - 'controls', 'plottings', 'parameters')
Alexandre Messa (some suggestions) [4 months]
Davoud Taghawi-Nejad (early-on pontual suggestion)

### How do I get set up?

We recommend using conda  and creating an environment that includes all libraries simultaneously.
Type on a terminal, after having downloaded and installed conda.

`conda create -n e36 python=3.6 gdal fiona geopandas numpy mkl scikit-learn numba joblib click click-plugins cligj
cycler descartes llvmlite munch numba pandas pyparsing pyproj python-dateutil pytz scipy shapely joblib Flask
Flask-WTF WTForms psutil -c conda-forge`

Using the above code will install the libraries.
Then, you have to activate the newly created environment with the command: activate <your_env>.
If any of the libraries were not available on conda-forge, use `pip install -U scikit-learn`, for example.

### Don't forget!

Extract/Unzip file mun_ibge_2014_latlong_wgs1984_fixed.zip

## How to run the model ##

### Configuration

To locally configure the simulation's parameters, create the following files as needed:

- `conf/run.py` for run-specific options, e.g. `OUTPUT_PATH` for where sim results are saved
- `conf/params.py` for simulation parameters, e.g. `LABOR_MARKET`.

The default options are in `conf/default/`, refer to those for what values can be set.

### Parallelization and multiple runs

These optional arguments are available for all the run commands:

- `-n` or `--runs` to specify how many times to run the simulation.
- `-c` or `--cpus` to specify number of CPUs to use when running multiple times. Use `-1` for all cores (default).

### Running

```
python main.py run
```

Example:

```
python main.py -c 2 -n 10 run
```

#### Sensitivity analysis

Runs simulation over a range of values for a specific parameter. For continuous parameters, the syntax is
`NAME:MIN:MAX:NUMBER_STEPS`. For boolean parameters, just provide the parameter name.

Example:

```
python main.py sensitivity ALPHA:0:1:7
```

Will run the simulation once for each value `ALPHA=0`, `ALPHA=0.17`, `ALPHA=0.33`, ... `ALPHA=1`.

Example:

```
python main.py sensitivity WAGE_IGNORE_UNEMPLOYMENT
```

Will run the simulation once for each value `WAGE_IGNORE_UNEMPLOYMENT=True` & `WAGE_IGNORE_UNEMPLOYMENT=False`.

You can also set up multiple sensitivity runs at once.

For example:

```
python main.py sensitivity ALPHA:0:1:0.1 WAGE_IGNORE_UNEMPLOYMENT
```

is equivalent to running the previous two examples in sequence.


#### Distributions

Runs simulation over a different distribution combinations: `ALTERNATIVE0: True/False, FPM_DISTRIBUTION: True/False`.

Example:

```
python main.py -n 2 -c 2 distributions
```


#### ACPs

Runs simulation over a different ACPs.

Example:

```
python main.py -n 2 -c 2 acps
```

#### Regenerating plots

You can regenerate plots for a set of runs by using:

```
python main.py make_plots /path/to/output
```

In Windows, make sure to use double quotes " " and backward slashes as in:

```
python main.py make_plots
"..\run__2017-11-01T11_59_59.240250_bh"
```

### Running the web interface

There is a preliminary web interface in development.

To run the server:

```
python main.py web
```

Then open `localhost:5000` in your browser.

---

### Last written documentation
arxiv.org/1702.03226v2.pdf AAMAS/ABMUS text
arxiv.org/1609.03996v1 SEAL operational manual

### Major changes since then
1. Firms no longer have FIXED salaries scheme. Really depends on sale. Major general improvements
2. Five TAXES introduced: consumption, labor, firm, real estate transaction, property
3. Also FOUR schemes of TAXES distribution among municipalities: multiple regional testing and modeling of taxes
distribution (multi_ACP_alternate)
4. Endogenous prices setting in a sticker manner
5. Decision-making of the firm profits hire, otherwise fire

### Next major move
TRANSPORT SYSTEMS or initial approach (such as BUS or CAR choices, related to income and time/productivity)

### MAJOR misses
1. Credit market
2. Exogenous regional MIGRATION
3. Housing rent market
4. Sectors and products variety

### Initial reference ###
* Based on Lengnick, 2013. Agent-based  macroeconomics:  A  baseline  model.
* Journal of Economic Behavior & Organization

### Distinctions from Lengnick, 2013 ###
1. Households are FIXED, but families can move into other households
2. We have either four or one government institution that collects taxes and improves quality of life index
3. Wage is paid to the agent, not on the household. However, consumption is based on families' average money
4. There is no fixed structure for the working-consumption network. Distance is used instead.
5. Different wage mechanism

### What is this repository for?
* Public Policy analysis
