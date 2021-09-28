"""Functionality to visualize apps"""

from __future__ import annotations

import dataclasses
import itertools
from typing import Callable, Generic, Iterable, Iterator, Optional, Sequence, Union

import more_itertools
import networkx as nx

from diagv.typing_utils import AdjacencyListT, HashableT, NormalizedAdjacencyList


def text_art(
    digraph: nx.DiGraph,
    ordering: Optional[Sequence[HashableT]] = None,
    fmt: Callable[[HashableT], str] = str,
) -> str:
    try:
        nx.find_cycle(digraph)
    except nx.NetworkXNoCycle:
        pass
    else:
        NotImplementedError("Only DAGs are supported so far")

    if ordering is None:
        ordering = list(nx.topological_sort(digraph))

    col2width = {i: len(fmt(v)) for i, v in enumerate(ordering)}
    cells = _cells(digraph, ordering)
    return "".join(_fmt_cells(cells, col2width, fmt))


def _nodes(graph: AdjacencyListT[HashableT]) -> Iterator[HashableT]:
    """Yield nodes in graph in reproducible order"""
    return more_itertools.unique_everseen(itertools.chain(graph, *graph.values()))


def _inverted(
    graph: AdjacencyListT[HashableT],
) -> NormalizedAdjacencyList[HashableT]:
    """Return graph with all arrows reverted"""
    result: NormalizedAdjacencyList[HashableT] = {node: set() for node in _nodes(graph)}
    for node in result:
        for adjacent in graph.get(node, []):
            result[adjacent].add(node)
    return result


class Token(str):
    ...


SECTION = Token("-")
INTERSECTION = Token("+")
OVERPASS = Token("|")
PADDING = Token(" ")
NOTHING = Token("")


@dataclasses.dataclass(frozen=True)
class Cell(Generic[HashableT]):
    ll: Token
    lr: Token
    cc: Union[HashableT, Token]
    rr: Token


def _cells(
    digraph: nx.DiGraph, order: Sequence[HashableT]
) -> Iterator[Optional[Cell[HashableT]]]:
    node2position = {v: i for i, v in enumerate(order)}
    dpred_lists = {
        node2position[node]: [node2position[dpred] for dpred in dpreds]
        for node, dpreds in digraph.pred.items()
    }
    dsucc_lists = _inverted(dpred_lists)

    for row, row_node in enumerate(order):
        if row:
            yield None
        for col, col_node in enumerate(order):
            yield cell(row, col, dpred_lists, dsucc_lists, row_node)


def _above_has_direct_predecessor_to_the_right(row, col, dsucc_lists):
    return col in dsucc_lists[row]


def _above_has_direct_predecessor_after(row, col, dpred_lists):
    direct_predecessors = dpred_lists[col]
    return direct_predecessors and row < max(direct_predecessors)


def _right_has_direct_successor_above_or_before(row, col, dsucc_lists):
    direct_successors = dsucc_lists[row]
    return direct_successors and min(direct_successors) <= col


def _right_has_direct_successor_above_this(row, col, dsucc_lists):
    return col in dsucc_lists[row]


def _has_direct_predecessor(row, col, dpred_lists):
    assert row == col
    return dpred_lists[row]


def _has_direct_successor_before(row, col, dsucc_lists):
    assert row == col
    direct_successors = dsucc_lists[row]
    return direct_successors and max(direct_successors) < row


def _before_has_direct_successor_after(row, col, dsucc_lists):
    successors = itertools.chain.from_iterable(
        dsucc_lists.get(node, []) for node in range(row)
    )
    try:
        return col < max(successors)
    except ValueError:
        return False


def _below_has_direct_predecessor_to_the_left(row, col, dsucc_lists):
    return col in dsucc_lists[row]


def _below_has_direct_predecessore_before(row, col, dpred_lists):
    direct_predecessors = dpred_lists[col]
    return direct_predecessors and min(direct_predecessors) < row


def _left_has_direct_successor_after(row, col, dsucc_lists):
    direct_successors = dsucc_lists[row]
    return direct_successors and col < max(direct_successors)


def cell(row, col, dpred_lists, dsucc_lists, node):
    # before: any node in the quadrant II w.r.t. the current cell
    # after: any node in the quadrant IV w.r.t. the current cell
    # above: the node on the diagonal directly above the current cell
    # below: the node on the diagonal directly below the current cell
    # left: the node on the diagonal directly to the left of the current cell
    # right: the node on the diagonal directly to the right of the current cell
    if col < row:
        # bottom left half
        if _above_has_direct_predecessor_to_the_right(row, col, dsucc_lists):
            ll = INTERSECTION
        elif _above_has_direct_predecessor_after(row, col, dpred_lists):
            ll = OVERPASS
        elif _right_has_direct_successor_above_or_before(row, col, dsucc_lists):
            ll = SECTION
        elif col or dpred_lists[col]:
            ll = PADDING
        else:
            ll = NOTHING

        if _right_has_direct_successor_above_or_before(row, col, dsucc_lists):
            lr = SECTION
        elif col or dpred_lists[col]:
            lr = PADDING
        else:
            lr = NOTHING

        if _right_has_direct_successor_above_or_before(row, col, dsucc_lists):
            c = r = SECTION
        else:
            c = r = PADDING

    elif row == col:
        if _has_direct_predecessor(row, col, dpred_lists):
            ll = INTERSECTION
            lr = SECTION
        elif _has_direct_successor_before(row, col, dsucc_lists):
            ll = lr = SECTION
        elif col or dpred_lists[col]:
            ll = lr = PADDING
        else:
            ll = lr = NOTHING

        c = node

        if _left_has_direct_successor_after(row, col, dsucc_lists):
            r = SECTION
        elif _before_has_direct_successor_after(row, col, dsucc_lists):
            r = PADDING
        else:
            r = NOTHING
    else:
        # top right half
        if _below_has_direct_predecessor_to_the_left(row, col, dsucc_lists):
            ll = INTERSECTION
        elif _below_has_direct_predecessore_before(row, col, dpred_lists):
            ll = OVERPASS
        elif _left_has_direct_successor_after(row, col, dsucc_lists):
            ll = SECTION
        elif _before_has_direct_successor_after(row, col, dsucc_lists):
            ll = PADDING
        else:
            ll = NOTHING

        if _left_has_direct_successor_after(row, col, dsucc_lists):
            lr = c = r = SECTION
        elif _before_has_direct_successor_after(row, col, dsucc_lists):
            lr = c = r = PADDING
        else:
            lr = c = r = NOTHING

    return Cell(ll, lr, c, r)


def _fmt_cells(
    cells: Iterable[Optional[Cell]], col2width, fmt: Callable[[HashableT], str]
) -> Iterator[str]:
    row = col = 0
    for cell in cells:
        if cell is None:
            row += 1
            col = 0
            yield "\n"
        else:
            yield _fmt_cell(cell, col2width.get(col, 1), fmt)
            col += 1


def _fmt_cell(cell, width, fmt):
    return "".join(
        [
            _fmt_subcell(cell.ll, 1, fmt),
            _fmt_subcell(cell.lr, 1, fmt),
            _fmt_subcell(cell.cc, width, fmt),
            _fmt_subcell(cell.rr, 1, fmt),
        ]
    )


def _fmt_subcell(subcell: Union[HashableT, Token], width, fmt):
    if subcell is NOTHING:
        return ""
    elif subcell in {PADDING, SECTION}:
        return subcell * width
    elif subcell in {INTERSECTION, OVERPASS}:
        assert width == 1
        return subcell
    else:
        return f"{fmt(subcell)[:width]:.^{width}}"
