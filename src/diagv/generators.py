import networkx as nx

from diagv import misc


def dibull():
    return misc.digraph(
        {
            "0": "1",
            "1": "23",
            "2": "3",
            "3": "4",
        }
    )


def diline(n):
    return nx.DiGraph([(i, i + 1) for i in range(n - 1)])


def distar(n):
    if n < 0:
        return nx.freeze(nx.DiGraph([(i + 1, 0) for i in range(-n)]))
    return nx.DiGraph([(0, i + 1) for i in range(n)])


def ditutte_fragment():
    return misc.digraph(
        {
            "A": "BC",
            "B": "DE",
            "C": "EF",
            "D": "GH",
            "E": "I",
            "F": "JK",
            "G": "LM",
            "H": "IM",
            "I": "J",
            "J": "N",
            "K": "OP",
            "L": "OQ",
            "M": "N",
            "N": "O",
        }
    )


def ditutte():
    graph = nx.generators.tutte_graph()
    tree = nx.traversal.bfs_tree(graph, 0)
    order = list(nx.topological_sort(tree))
    return nx.DiGraph(
        [
            (head, tail) if order.index(head) < order.index(tail) else (tail, head)
            for (head, tail) in graph.edges
        ]
    )
