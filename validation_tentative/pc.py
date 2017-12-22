"""
pip install git+https://github.com/pgmpy/pgmpy.git
pip install wrapt

<http://pgmpy.chrisittner.de/2016/08/17/pc.html>
"""

import pandas as pd
import networkx as nx
from pgmpy.estimators import ConstraintBasedEstimator


def pc(mat):
    data = pd.DataFrame(mat)
    c = ConstraintBasedEstimator(data)
    model = c.estimate()

    # kinda hacky, but can't find a more direct way
    # of getting the adj matrix
    g = nx.DiGraph()
    g.add_nodes_from(model.nodes())
    g.add_edges_from(model.edges())

    # specify nodelist to maintain ordering
    # consistent with dataframe
    # TODO this is a non-weighted adjacency matrix,
    # but according to the paper, it might need to be? given
    # their signs are being checked
    return nx.adjacency_matrix(g, nodelist=data.columns).todense()
