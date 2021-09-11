"""Functionality to visualize apps"""
import graphlib
import itertools
from typing import (
    Callable,
    Dict,
    Hashable,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

_HashableT = TypeVar("_HashableT", bound=Hashable)
_AdjacencyListT = Mapping[_HashableT, Iterable[_HashableT]]


def _sorted_topolocial_guided(
    graph: _AdjacencyListT[_HashableT], reach
) -> Iterator[_HashableT]:
    sorter = graphlib.TopologicalSorter(graph)
    sorter.prepare()
    ready: List[_HashableT] = []
    while sorter.is_active():
        ready.extend(sorter.get_ready())
        node = min(ready, key=reach.__getitem__)
        sorter.done(node)
        ready.remove(node)
        yield node


def _sorted_topological(graph: _AdjacencyListT[_HashableT]) -> Tuple[_HashableT, ...]:
    """Return nodes in sorted order

    The order
    * guarantees that a node comes before all its successors,
    * attempts to minimize the length distance between adjacent nodes.
    """
    sorter = graphlib.TopologicalSorter(graph)
    # Greedy attempt at reducing the length of edges in the art
    # So far it minimizes the vertical component but ignores the horizontal component.
    direct_successors_lists = _inverted(graph)
    curr = tuple(sorter.static_order())
    for i in range(10):
        positions = {k: i for i, k in enumerate(curr)}
        reaches = {
            predecessor: max(
                [
                    positions[successor]
                    for successor in direct_successors_lists.get(predecessor, [])
                ],
                default=0,
            )
            for predecessor in curr
        }
        prev, curr = curr, tuple(_sorted_topolocial_guided(graph, reaches))
        if prev == curr:
            return curr
    raise RuntimeError("Failed to sort nodes in 10 rounds")


def art(
    graph: _AdjacencyListT[_HashableT],
    max_col_width: Optional[int] = None,
    fmt: Callable[[_HashableT], str] = lambda x: str(x),
) -> str:
    """Return ascii art representation of graph"""
    positions = {v: i for i, v in enumerate(_sorted_topological(graph))}
    names = [fmt(v) for v in positions]
    predecessor_lists = {
        positions[src]: [positions[dst] for dst in dsts] for src, dsts in graph.items()
    }
    sucessor_lists = _inverted(predecessor_lists)
    return "".join(
        _art(
            names,
            predecessor_lists,
            sucessor_lists,
            max(map(len, names)) if max_col_width is None else max_col_width,
        )
    )


def _above_has_successor_to_the_right(
    row: int,
    col: int,
    successor_lists: Mapping[int, Iterable[int]],
) -> Optional[int]:
    successors = itertools.chain.from_iterable(
        successor_lists.get(predecessor, []) for predecessor in range(row)
    )
    try:
        return col < max(successors)
    except ValueError:
        return False


def _art(
    names: Sequence[str],
    predecessor_lists: Mapping[int, Iterable[int]],
    successor_lists: Mapping[int, Iterable[int]],
    max_width: int,
) -> Iterator[str]:
    col_widths = [min(max_width, len(x)) for x in names]
    for row in range(len(names)):
        successors = successor_lists.get(row, [])
        if row:
            yield "\n"
        for col in range(len(names)):
            predecessors = predecessor_lists.get(col, [])
            col_width = col_widths[col]

            if col < row:
                ll = lr = cc = rr = " "
            elif row == col:
                if predecessors:
                    ll = "+"
                    lr = "-"
                else:
                    ll = lr = " "

                cc = names[row]

                if successors:
                    rr = "-"
                elif _above_has_successor_to_the_right(row, col, successor_lists):
                    rr = " "
                else:
                    rr = ""
            else:
                if row in predecessors:
                    ll = "+"
                elif predecessors and min(predecessors) < row:
                    ll = "|"
                elif successors and col < max(successors):
                    ll = "-"
                elif _above_has_successor_to_the_right(row, col, successor_lists):
                    ll = " "
                else:
                    ll = ""

                if successors and col < max(successors):
                    lr = cc = rr = "-"
                elif _above_has_successor_to_the_right(row, col, successor_lists):
                    lr = cc = rr = " "
                else:
                    lr = cc = rr = ""

            if col:
                yield ll
                yield lr
            yield lr * (col_width - len(cc)) + cc[:col_width]
            yield rr


def _inverted(
    graph: Mapping[_HashableT, Iterable[_HashableT]]
) -> Mapping[_HashableT, Iterable[_HashableT]]:
    result: Dict[_HashableT, List[_HashableT]] = {}
    for k, vs in graph.items():
        result.setdefault(k, [])
        for v in vs:
            result.setdefault(v, [])
            result[v].append(k)
    return result
