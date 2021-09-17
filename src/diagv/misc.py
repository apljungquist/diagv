import networkx as nx

from diagv.typing_utils import AdjacencyListT


def digraph(graph: AdjacencyListT, order=1) -> nx.DiGraph:
    return nx.DiGraph((k, v)[::order] for k, vs in graph.items() for v in vs)


def raise_for_cyclic(digraph: nx.DiGraph) -> None:
    try:
        nx.find_cycle(digraph)
    except nx.NetworkXNoCycle:
        return
    NotImplementedError("Only DAGs are supported so far")
