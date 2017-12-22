import numpy as np
from scipy import stats
from . import lingam#, pc
# from statsmodels.tsa.api import VAR


def validate(rw_data, ab_data, rw_data_len, significance_level):
    """validate ABM output against real data"""
    vars = list(rw_data.keys())
    ab_data = align_tseries(ab_data, rw_data_len)

    # TODO missing augmented dickey-fuller test for unit root

    # ideally these should all be >= 0.90
    print('ergodicity:', ergodicity(ab_data, rw_data_len))
    print('statistical equilirbium:', statistical_equilibrium(ab_data, rw_data_len))

    results = []
    rw_adj_mat, rw_lag_order = svar(rw_data, significance_level)
    for data in ab_data:
        adj_mat, lag_order = svar(data, significance_level)
        lag_order_max = max(rw_lag_order, lag_order)

        # zero-out misaligned intervals
        if lag_order_max == rw_lag_order and lag_order < lag_order_max:
            for i in range(lag_order, lag_order_max + 1):
                adj_mat[i] = 0
        elif lag_order_max == lag_order and rw_lag_order < lag_order_max:
            for i in range(rw_lag_order, lag_order_max + 1):
                rw_adj_mat[i] = 0

        K = len(vars)
        score = 0
        for i in range(lag_order_max):
            for j in range(K):
                for k in range(K):
                    score += int(np.sign(rw_adj_mat[i, j, k]) == np.sign(adj_mat[i, j, k]))

        # bound between [0, 1]
        sign_based_similarity = score/(K**2 * lag_order_max)
        results.append({
            'sign_based_sim': sign_based_similarity
        })
    return results


def align_tseries(ab, rw_data_len):
    """align ABM data to match real-world data"""
    adjusted = []
    for run in ab:
        d = {k: v[-rw_data_len:] for k, v in run.items()}
        adjusted.append(d)
    return adjusted


def ks_test(rvs1, rvs2, significance_level=0.05):
    """kolmogorov-smirnov test. if returns True, then keep, else reject"""
    d, p = stats.ks_2samp(rvs1, rvs2)
    return p > significance_level


def ergodicity(runs, rw_data_len):
    trials = len(runs) * rw_data_len
    results = {}
    vars = list(runs[0].keys())
    for var in vars:
        accepted = 0
        mat = np.array([r[var] for r in runs])
        for sample in mat:
            for ensemble in mat.T:
                if ks_test(sample, ensemble):
                    accepted += 1
        results[var] = accepted/trials
    return results


def statistical_equilibrium(runs, rw_data_len):
    trials = (rw_data_len * (rw_data_len - 1))/2
    results = {}
    vars = list(runs[0].keys())
    for var in vars:
        accepted = 0
        mat = np.array([r[var] for r in runs])
        for i, ensemble_a in enumerate(mat.T):
            for j, ensemble_b in enumerate(mat.T):
                if i > j:
                    continue
                elif ks_test(ensemble_a, ensemble_b):
                    accepted += 1
        results[var] = accepted/trials
    return results


def svar(data, significance_level):
    # arrange so rows are a time slice,
    # columns are a variable
    data_mat = np.stack([var for var in data.values()], axis=1)
    model = VAR(data_mat)
    results = model.fit(ic='bic') # 'aic', 'hqic', or 'bic'
    lag_order = results.k_ar # i.e. p_RW or p_AB_i
    print('lag order:', lag_order)

    # TODO missing "cointegrating relationships" part

    n_normal = 0
    for var in results.resid.T:
        # to use lingam, these must basically all be non-gaussian
        # (max of one can be gaussian)
        # shapiro-wilk test for normality
        w, p = stats.shapiro(var)
        n_normal += int(p > significance_level) # -> true: evidence for normality

        # j, p = stats.jarque_bera(var)
        # print(p > significance_level)
        # I think A_i = var
        # for lingam.py

    gaussian = n_normal > 1
    print('gaussian:', gaussian)

    if not gaussian:
        # if non-gaussian:
        adj_mat = lingam.lingam(results.resid)
        #print(adj_mat.shape)
    else:
        pass
        # TODO this needs to return a 3-tensor?
        # commenting this out b/c can't get PC to work correctly
        #adj_mat = pc.pc(results.resid)
        #print(adj_mat.shape)

    return adj_mat, lag_order


