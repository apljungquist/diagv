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
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

_HashableT = TypeVar("_HashableT", bound=Hashable)
_AdjacencyListT = Mapping[_HashableT, Iterable[_HashableT]]


def _score(graph: _AdjacencyListT[_HashableT], order: Sequence[_HashableT]) -> int:
    return sum(
        (token[:2] == ("|", "-")) + (token[0] == "|") + (token[2] == "-")
        for token in _art_hashable_tokens(graph, order)
        if isinstance(token, tuple)
    )


def _refined_topolocial(
    graph: _AdjacencyListT[_HashableT], start: Sequence[_HashableT]
) -> Sequence[_HashableT]:
    # This is ridiculously slow for non-trivial examples
    # It is also prone to getting stuck in local optima since it only considers moving
    # one node at a time.
    curr_order = tuple(start)
    curr_score = _score(graph, curr_order)
    prev_score = curr_score + 1
    while curr_score < prev_score:
        prev_score = curr_score
        prev_order = curr_order
        # Move forward
        for cut_at, cut in enumerate(prev_order):
            left_of_cut, right_of_cut = prev_order[:cut_at], prev_order[(cut_at + 1) :]
            for move_by, left_neighbor in enumerate(right_of_cut, 1):
                left_of_insert, right_of_insert = (
                    right_of_cut[:move_by],
                    right_of_cut[move_by:],
                )
                if cut in graph.get(left_neighbor, []):
                    break  # Maintain topological order
                order = left_of_cut + left_of_insert + (cut,) + right_of_insert
                score = _score(graph, order)
                if score <= curr_score:
                    curr_score = score
                    curr_order = order
        # Move backward
        for cut_at, cut in list(enumerate(prev_order))[::-1]:
            left_of_cut, right_of_cut = prev_order[:cut_at], prev_order[(cut_at + 1) :]
            for move_by, right_neighbor in list(enumerate(left_of_cut, 1))[::-1]:
                left_of_insert, right_of_insert = (
                    left_of_cut[: move_by - 1],
                    left_of_cut[move_by - 1 :],
                )
                if right_neighbor in graph.get(cut, []):
                    break
                order = left_of_insert + (cut,) + right_of_insert + right_of_cut
                score = _score(graph, order)
                if score < curr_score:
                    curr_score = score
                    curr_order = order
    return curr_order


def _sorted_topological(graph: _AdjacencyListT[_HashableT]) -> Tuple[_HashableT, ...]:
    """Return nodes in sorted order

    The order
    * guarantees that a node comes before all its successors,
    * attempts to minimize the length distance between adjacent nodes.
    """
    sorter = graphlib.TopologicalSorter(graph)
    return tuple(_refined_topolocial(graph, tuple(sorter.static_order())))


def art(
    graph: _AdjacencyListT[_HashableT],
    max_col_width: Optional[int] = None,
    fmt: Callable[[_HashableT], str] = lambda x: str(x),
) -> str:
    """Return ascii art representation of graph"""
    order = _sorted_topological(graph)
    return "".join(_art_str_tokens(graph, order, fmt, max_col_width))


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


def _art_str_tokens(
    graph: _AdjacencyListT[_HashableT],
    order,
    fmt,
    max_col_width,
) -> Iterator[str]:
    tokens = _art_hashable_tokens(graph, order)
    names = {v: fmt(v) for v in order}
    reserved = {"-", " ", ""}
    assert not reserved & set(names.values())
    if max_col_width is None:
        max_col_width = max(map(len, names.values()))
    col_widths = {
        col: min(len(names[node]), max_col_width) for col, node in enumerate(order)
    }

    row = col = 0
    for token in tokens:
        if token == "\n":
            row += 1
            col = 0
            yield token
        else:
            col_width = col_widths[col]
            ll, lr, cc, rr = token
            if cc in reserved:
                cc = cc * col_width
            else:
                cc = f"{names[cc][:col_width]:{col_width}}"
            yield ll + lr + cc + rr
            col += 1


def _art_hashable_tokens(
    graph: _AdjacencyListT[_HashableT],
    order: Sequence[_HashableT],
) -> Iterator[Union[Literal["\n"], Tuple[str, str, Union[_HashableT, str], str]]]:
    cc: Union[_HashableT, str]  # help mypy

    positions = {v: i for i, v in enumerate(order)}
    predecessor_lists = {
        positions[src]: [positions[dst] for dst in dsts] for src, dsts in graph.items()
    }
    successor_lists = _inverted(predecessor_lists)
    for row in range(len(order)):
        successors = successor_lists.get(row, [])
        if row:
            yield "\n"
        for col in range(len(order)):
            predecessors = predecessor_lists.get(col, [])
            if col < row:
                ll = lr = cc = rr = " "
            elif row == col:
                if predecessors:
                    ll = "+"
                    lr = "-"
                else:
                    ll = lr = " "

                cc = order[row]

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

            if not col:
                ll = lr = ""

            yield ll, lr, cc, rr


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
