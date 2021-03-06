"""
This is the model that organizes the full simulation.
It handles all the choices of the model, usually set at the Parameters module.
Those include the need to import data, save data or produce output.
At the end, it calls the module 'have_a_go' which actually starts the simulation
Time dynamics is given by the module 'time_iteration' which is called from 'have_a_go'.
Running multiple simulations or sensitivity analysis should be run from the group of
'control...' modules.

Disclaimer:
This code was generated for research purposes only.
It is licensed under GNU v3 license
"""
import os
import copy
import conf
import json
import click
import logging
import validation_tentative
import numpy as np
import pandas as pd
from glob import glob
from analysis import report
from datetime import datetime
from simulation import Simulation
from collections import defaultdict
from itertools import product, chain
from joblib import Parallel, delayed
from analysis.plotting import Plotter
from web import app


logger = logging.getLogger('main')
logging.basicConfig(level=logging.INFO)


def conf_to_str(conf, delimiter='\n'):
    """Represent a configuration dict as a string"""
    parts = []
    for k, v in sorted(conf.items()):
        v = ','.join(v) if isinstance(v, list) else str(v)
        part = '{}={}'.format(k, v)
        parts.append(part)
    return delimiter.join(parts)


def single_run(params, path):
    """Run a simulation once for given parameters"""
    sim = Simulation(params, path)
    sim.run()

    if conf.RUN['PLOT_EACH_RUN']:
        logger.info('Plotting run...')
        plot([('run', path)], os.path.join(path, 'plots'), params, sim=sim)


def multiple_runs(overrides, runs, cpus, output_dir):
    """Run multiple configurations, each `runs` times"""
    logger.info('Running simulation {} times'.format(len(overrides) * runs))

    # calculate output paths and params with overrides
    paths = [os.path.join(output_dir, conf_to_str(o, delimiter=';'))
             for o in overrides]
    params = []
    for o in overrides:
        p = copy.deepcopy(conf.PARAMS)
        p.update(o)
        params.append(p)

    # run simulations in parallel
    jobs = [
        [(delayed(single_run)(p, os.path.join(path, str(i)))) for i in range(runs)]
        for p, path in zip(params, paths)]
    jobs = chain(*jobs)
    if cpus == 1:
        # run serially if cpus==1, easier debugging
        [fn(*args) for fn, args, _ in jobs]
    else:
        Parallel(n_jobs=cpus)(jobs)

    logger.info('Averaging run data...')
    results = []
    for path, params, o in zip(paths, params, overrides):
        # save configurations
        with open(os.path.join(path, 'conf.json'), 'w') as f:
            json.dump({
                'RUN': conf.RUN,
                'PARAMS': params
            }, f)

        # average run data and then plot
        runs = [p for p in glob('{}/*'.format(path)) if os.path.isdir(p)]
        avg_path = average_run_data(path, avg='median')

        # return result data, e.g. paths for plotting
        results.append({
            'path': path,
            'runs': runs,
            'params': params,
            'overrides': o,
            'avg': avg_path,
            'avg_type': 'median'
        })
    with open(os.path.join(output_dir, 'meta.json'), 'w') as f:
        json.dump(results, f)

    plot_results(output_dir)

    # link latest sim to convenient path
    latest_path = os.path.join(conf.RUN['OUTPUT_PATH'], 'latest')
    if os.path.isdir(latest_path):
        os.remove(latest_path)

    try:
        os.symlink(output_dir, latest_path)
    except OSError: # Windows requires special permissions to symlink
        pass

    logger.info('Finished.')
    return results


def average_run_data(path, avg='mean'):
    """Average the run data for a specified output path"""
    output_path = os.path.join(path, 'avg')
    os.makedirs(output_path)

    # group by filename
    file_groups = defaultdict(list)
    for file in glob(os.path.join(path, '**/*.csv')):
        # by default, only average stats files.
        # the other files become way too large
        # and take a very long time to average.
        if 'stats' in file or conf.RUN['AVERAGE_ALL_DATA']:
            fname = os.path.basename(file)
            file_groups[fname].append(file)

    # merge
    for fname, files in file_groups.items():
        dfs = []
        for f in files:
            df = pd.read_csv(f,  sep=';', decimal='.', header=None).apply(pd.to_numeric, errors='coerce')
            dfs.append(df)
        df = pd.concat(dfs)
        df = df.groupby(df.index)
        df = getattr(df, avg)()
        df[0] = df[0].astype(int) # first col is month and should be int
        df.to_csv(os.path.join(output_path, fname), header=False, index=False, sep=';')
    return output_path


def plot(input_paths, output_path, params, styles=None, sim=None):
    """Generate plots based on data in specified output path"""
    plotter = Plotter(input_paths, output_path, params, styles=styles)

    if conf.RUN['DESCRIPTIVE_STATS_CHOICE']:
        report.stats('')

    if conf.RUN['SAVE_PLOTS_FIGURES']:
        plotter.plot_general()
        if sim is not None or conf.RUN['AVERAGE_ALL_DATA']:
            plotter.plot_regional_stats()

        if conf.RUN['SAVE_AGENTS_DATA_MONTHLY'] \
                or conf.RUN['SAVE_AGENTS_DATA_QUARTERLY'] \
                or conf.RUN['SAVE_AGENTS_DATA_ANNUALLY']:
            if sim is not None or conf.RUN['AVERAGE_ALL_DATA']:
                plotter.plot_firms_diagnosis()

    # Checking whether to plot or not
    if conf.RUN['SAVE_SPATIAL_PLOTS'] and sim is not None:
        plotter.plot_geo(sim, 'final')


def plot_runs_with_avg(run_data):
    """Plot results of simulations sharing a configuration,
    with their average results"""
    # load avg data path, then paths for individual runs
    # and pair with labels
    labels_paths = [(run_data['avg_type'], run_data['avg'])] + list(enumerate(run_data['runs']))

    # set the avg to solid and the rest to dashed lines
    styles = ['-'] + ['--' for _ in run_data['runs']]

    # output to the run directory + /plots
    output_path = os.path.join(run_data['path'], 'plots')

    # plot
    plot(labels_paths, output_path, {}, styles)


def plot_results(output_dir):
    """Plot results of multiple simulations"""
    logger.info('Plotting results...')
    results = json.load(open(os.path.join(output_dir, 'meta.json'), 'r'))
    avgs = []
    for r in results:
        plot_runs_with_avg(r)

        # group averages, with labels, to plot together
        label = conf_to_str(r['overrides'], delimiter='\n')
        avgs.append((label, r['avg']))

    # plot averages
    if len(avgs) > 1:
        output_path = os.path.join(output_dir, 'plots')
        plot(avgs, output_path, {})


def impute(data):
    """very naive/imprecise data imputation, can be improved"""
    return data.interpolate(limit_direction='both').fillna(method='bfill')


def gen_output_dir(command):
    timestamp = datetime.utcnow().isoformat().replace(':', '_')
    run_id = '{}__{}'.format(command, timestamp)
    return os.path.join(conf.RUN['OUTPUT_PATH'], run_id)


@click.group()
@click.pass_context
@click.option('-n', '--runs', help='Number of simulation runs', default=1)
@click.option('-c', '--cpus', help='Number of CPU cores to use', default=-1)
@click.option('-p', '--params', help='JSON of params override')
@click.option('-r', '--config', help='JSON of run config override')
def main(ctx, runs, cpus, params, config):
    if not conf.RUN['SAVE_AGENTS_DATA_MONTHLY'] \
            and not conf.RUN['SAVE_AGENTS_DATA_QUARTERLY'] \
            and not conf.RUN['SAVE_AGENTS_DATA_ANNUALLY']:
        logger.warn('Warning!!! Are you sure you do NOT want to save AGENTS\' data?')

    # apply any top-level overrides, if specified
    params = json.loads(params) if params is not None else {}
    config = json.loads(config) if config is not None else {}
    conf.PARAMS.update(params) # applied per-run
    conf.RUN.update(config)    # applied globally

    ctx.obj = {
        'output_dir': gen_output_dir(ctx.invoked_subcommand),
        'runs': runs,
        'cpus': cpus
    }


@main.command()
@click.pass_context
def run(ctx):
    """
    Basic run(s) with different seeds
    """
    multiple_runs([{}], ctx.obj['runs'], ctx.obj['cpus'], ctx.obj['output_dir'])


@main.command()
@click.argument('params', nargs=-1)
@click.pass_context
def sensitivity(ctx, params):
    """
    Continuous param syntax: NAME:MIN:MAX:STEP
    Boolean param syntax: NAME
    """
    for param in params:
        ctx.obj['output_dir'] = gen_output_dir(ctx.command.name)

        # if ':' present, assume continuous param
        if ':' in param:
            p_name, p_min, p_max, p_step = param.split(':')
            p_min, p_max, p_step = (float(v) for v in [p_min, p_max, p_step])
            p_vals = np.linspace(p_min, p_max, p_step)
            p_vals = np.round(p_vals, 2)

        # else, assume boolean
        else:
            p_name = param
            p_vals = [True, False]
        confs = [{p_name: v} for v in p_vals]

        # fix the same seed for each run
        conf.RUN['KEEP_RANDOM_SEED'] = False

        logger.info('Sensitivity run over {} for values: {}, {} run(s) each'.format(p_name, p_vals, ctx.obj['runs']))
        multiple_runs(confs, ctx.obj['runs'], ctx.obj['cpus'], ctx.obj['output_dir'])


@main.command()
@click.pass_context
def distributions(ctx):
    """
    Run across ALTERNATIVE0/FPM_DISTRIBUTION combinations
    """
    confs = [{
        'ALTERNATIVE0': ALTERNATIVE0,
        'FPM_DISTRIBUTION': FPM_DISTRIBUTION
    } for ALTERNATIVE0, FPM_DISTRIBUTION in product([True, False], [True, False])]

    logger.info('Varying distributions, {} run(s) each'.format(ctx.obj['runs']))
    multiple_runs(confs, ctx.obj['runs'], ctx.obj['cpus'], ctx.obj['output_dir'])


@main.command()
@click.pass_context
def acps(ctx):
    """
    Run across ACPs
    """
    confs = []
    exclude_list = []
    # ACPs with just one municipality
    #exclude_list = ['CAMPO GRANDE', 'CAMPO DOS GOYTACAZES', 'FEIRA DE SANTANA', 'MANAUS',
                    #'PETROLINA - JUAZEIRO', 'TERESINA', 'UBERLANDIA']
    all_acps = pd.read_csv('input/ACPs_BR.csv', sep=';', header=0)
    acps = set(all_acps.loc[:, 'ACPs'].values.tolist())
    acps = list(acps)
    for acp in acps:
        if acp not in exclude_list:
            confs.append({
                'PROCESSING_ACPS': [acp]
            })
    logger.info('Running over ACPs, {} run(s) each'.format(ctx.obj['runs']))
    multiple_runs(confs, ctx.obj['runs'], ctx.obj['cpus'], ctx.obj['output_dir'])



@main.command()
@click.argument('output_dir')
def make_plots(output_dir):
    """
    (Re)generate plots for an output directory
    """
    plot_results(output_dir)


@main.command()
@click.option('-s', '--sig-level', help='Significance level', default=0.05)
@click.pass_context
def validate(ctx, sig_level):
    """
    Validate simulation output
    """
    df = pd.read_csv('validating_data/general.csv')
    rw_data = {
        'inflation': impute(df['real_inflation']).values,
        'consumption': impute(df['real_consumption']).values
    }

    ab_data = [{
        'inflation': impute(df['model_inflation']).values,
        'consumption': impute(df['model_consumption']).values
    }]
    rw_data_len = len(df['real_inflation'].values)
    results = validation_tentative.validate(rw_data, ab_data, rw_data_len, sig_level)
    print(results)


@main.command()
def web():
    app.run(debug=True)


if __name__ == '__main__':
    main()
