import numpy as np
from sklearn.decomposition import FastICA

T=10
K=3
arr = np.random.random(size=(T,K))


def lingam(arr):
    T, K = arr.shape
    ica = FastICA()
    E = ica.fit_transform(arr)
    P = ica.mixing_
    assert E.shape == (T, K)
    assert P.shape == (K, K)

    gamma = np.linalg.inv(P)

    # permute gamma rows to minimize diagonal sum
    permutation = min_diag_permutation(gamma)
    gamma = gamma[permutation]

    # divide each row by its diagonal element
    for i, row in enumerate(gamma):
        row /= row[i]

    I = np.identity(gamma.shape[0])
    B = I - gamma

    # approximate lower-triangular version of B
    # routine for permuting as described in Shimizu et al., 2006
    m = B.shape[0]
    n = int((m*(m+1))/2)
    B = zero_min_elements(B, n)
    permutation = False
    while not permutation:
        permutation = lower_tri_permute(B)
        B = zero_min_elements(B, 1, exclude_zero=True)
    B = B[permutation]

    # estimate structure for each time period
    results = []
    for A in arr:
        gamma_i = (I - B) * A
        results.append(gamma_i)
    return np.stack(results)



def sum_diag(mat, path):
    """sum diagonal of a matrix
    given a row permutation (path)"""
    return np.diag(mat[path]).sum()


def successors(rows, path):
    """successors are rows not already in the path"""
    return [i for i in rows if i not in path]


def min_diag_permutation(mat):
    """find row permutation that gives
    a minimum diagonal sum. must be a square matrix.
    this is faster than brute-force searching over all
    row permutations."""
    m = mat.shape[0]
    rows = list(range(m))

    # initialize paths
    paths = [[i] for i in rows]

    while True:
        # sort and pop shortest path
        # TODO can cache these sums
        paths = sorted(paths, key=lambda p: sum_diag(mat, p))
        path = paths.pop(0)

        # if path is complete, then it's the shortest
        if len(path) == m:
            return path

        # expand path to successors
        paths.extend([path + [succ] for succ in successors(rows, path)])


def zero_min_elements(mat, n, exclude_zero=False):
    # get raveled indices of n min elements
    if exclude_zero:
        # get mins, excluding zeros
        n += (mat.size - np.count_nonzero(mat))
    idx = np.argsort(mat, axis=None)[:n]
    np.ravel(mat)[idx] = 0
    return mat


def all_zero_rows(mat):
    return np.where(~mat.any(axis=1))[0]


def lower_tri_permute(mat):
    permutation = []
    m = mat.shape[0]
    rows = list(range(m))
    mat_ = np.copy(mat)
    while rows:
        zero_rows = all_zero_rows(mat_)
        if zero_rows.size == 0:
            return False
        local_row = zero_rows[0]
        orig_row = rows[local_row]
        mat_ = np.delete(np.delete(mat_, local_row, axis=-1), local_row, axis=0) # remove ith row and column
        rows.remove(orig_row)
        permutation.append(orig_row)
    return permutation
