"""Functionality to visualize apps"""
from __future__ import annotations

import collections
import functools
import itertools
import math
import operator
from typing import Callable, Dict, FrozenSet, Generic, Iterator, Sequence, Set, Tuple

import more_itertools
import networkx as nx

from diagv import misc
from diagv.typing_utils import AdjacencyListT, HashableT, NormalizedAdjacencyList


def _nodes(graph: AdjacencyListT[HashableT]) -> Iterator[HashableT]:
    """Yield nodes in graph in reproducible order"""
    return more_itertools.unique_everseen(itertools.chain(graph, *graph.values()))


def _normalized(
    graph: AdjacencyListT[HashableT],
) -> NormalizedAdjacencyList[HashableT]:
    """Return graph in form that is amenable to many computations"""
    return {node: set(graph.get(node, [])) for node in _nodes(graph)}


def _inverted(
    graph: AdjacencyListT[HashableT],
) -> NormalizedAdjacencyList[HashableT]:
    """Return graph with all arrows reverted"""
    result: NormalizedAdjacencyList[HashableT] = {node: set() for node in _nodes(graph)}
    for node in result:
        for adjacent in graph.get(node, []):
            result[adjacent].add(node)
    return result


def _reachables(
    graph: AdjacencyListT[HashableT], origin: HashableT
) -> Iterator[HashableT]:
    """Yield all nodes that are reachable from `origin`"""
    done: Set[HashableT] = set()
    remaining = collections.deque(graph.get(origin, []))
    while remaining:
        node = remaining.popleft()
        yield node
        if node not in done:
            done.add(node)
            remaining.extend(graph.get(node, []))


def _reachability(
    graph: AdjacencyListT[HashableT],
) -> Dict[HashableT, Set[HashableT]]:
    """Return mapping from each node to all its descendants"""
    return {node: set(_reachables(graph, node)) for node in graph}


class _Graph(Generic[HashableT]):
    """Precomputed collection of graph properties

    These are frequently accessed by the algorithms and having them precomputed speeds
    up execution.
    """

    def __init__(self, graph: AdjacencyListT[HashableT]) -> None:
        self.nodes = list(
            more_itertools.unique_everseen(itertools.chain(graph, *graph.values()))
        )
        self.nodes_set = frozenset(self.nodes)
        self.node2direct_predecessors = _normalized(graph)
        self.node2direct_successors = _inverted(graph)
        self.node2predecessors = _reachability(self.node2direct_predecessors)
        self.node2successors = _reachability(self.node2direct_successors)


def marginal_cost(
    graph: _Graph[HashableT],
    before: Sequence[HashableT],
    this: HashableT,
    after: FrozenSet[HashableT],
) -> int:
    node2position = {v: i for i, v in enumerate(before)}
    dpreds = graph.node2direct_predecessors[this]
    dpred_positions = [
        node2position[direct_predecessor] for direct_predecessor in dpreds
    ]
    first_dpred_pos = min(dpred_positions, default=len(before))
    intermediate = [
        (
            len(graph.node2direct_successors[other] & after),
            (first_dpred_pos < other_pos and other not in dpreds),
        )
        # Before is often longer than after since invocations with short before get
        # cached. Is it possible to iterate over after instead? Equivalent complexity
        # but should get rid of one python constant
        for other_pos, other in enumerate(before)
    ]
    cost_from_other = sum(
        [
            num_extension + bool(num_extension) * extension_is_interaction
            for num_extension, extension_is_interaction in intermediate
        ]
    )
    return cost_from_other


@functools.lru_cache(maxsize=100_000)
def cost(
    graph: _Graph[HashableT],
    prefix: Sequence[HashableT],
    unvisited: FrozenSet[HashableT],
) -> int:
    """Returns a number quantifying how not nice the graph would look when drawn

    The returned number is a lower bound on the cost of any path that starts with `prefix`.
    I.e. there is no way to add the unvisited nodes to the prefix and get a lower cost.
    A tighter bound allows more effective pruning.
    """
    if not prefix:
        return 0
    before = prefix[:-1]
    this = prefix[-1]
    return cost(graph, before, unvisited | {this}) + marginal_cost(
        graph, before, this, unvisited
    )


def _topological_orderings(
    g,
    path: Tuple[HashableT, ...],
    should_be_pruned: Callable[[Tuple[HashableT, ...], FrozenSet[HashableT]], bool],
) -> Iterator[Tuple[HashableT, ...]]:
    """Yield topological orderings of graph"""
    visited = set(path)
    for node in g.nodes:
        if node in visited:
            continue

        # Prune branches that would not be ordered
        if g.node2predecessors[node] - visited:
            continue

        new_path = path + (node,)
        new_unvisited = g.nodes_set - visited - {node}
        # Prune branches that are guaranteed to be suboptimal
        if should_be_pruned(new_path, new_unvisited):
            continue

        if new_unvisited:
            yield from _topological_orderings(g, new_path, should_be_pruned)
        else:
            yield new_path


def sorted_topological(digraph: nx.DiGraph) -> Tuple[HashableT, ...]:
    """Return an optimal topological ordering

    Not that there may be several others that are equally good.
    """
    misc.raise_for_cyclic(digraph)
    return min(as_found(digraph), key=operator.itemgetter(0))[1]


def as_found(digraph: nx.DiGraph) -> Iterator[Tuple[int, Tuple[HashableT, ...]]]:
    """Return good topological orderings as they are found

    Each ordering is no worse than the previous.
    """
    misc.raise_for_cyclic(digraph)
    g = _Graph(digraph.pred)
    prev_best = math.inf

    def prune(new_path, new_unvisited):
        return prev_best < cost(g, new_path, new_unvisited)

    for order in _topological_orderings(g, (), prune):
        curr_best = cost(g, order, frozenset())
        yield curr_best, order
        assert curr_best <= prev_best
        prev_best = curr_best
