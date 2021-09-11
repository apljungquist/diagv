"""Functionality to play, record and replay the app dag

Models app as a directed acyclic graph (DAG) in which
* data types are the nodes, and
* functions are the edges, each function can represent one or more edges.
"""
import graphlib
import itertools
from typing import (
    Any,
    Callable,
    Dict,
    Hashable,
    Iterable,
    List,
    Mapping,
    Protocol,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

_T = TypeVar("_T")
_HashableT = TypeVar("_HashableT", bound=Hashable)
_AdjacencyListT = Mapping[_HashableT, Iterable[_HashableT]]

_JsonObjectT = Dict[str, Any]
_JsonListT = List[Any]
_JsonSimpleT = Union[bool, float, int, None, str]
_JsonAnyT = Union[_JsonObjectT, _JsonListT, _JsonSimpleT]


class _SupportsToJsonP(Protocol):
    def to_json(self) -> _JsonAnyT:
        ...


class _SupportsFromJsonP(Protocol):
    @classmethod
    def from_json(cls: Type[_T], obj: _JsonAnyT) -> _T:
        ...


def _nodes(graph: _AdjacencyListT[_HashableT]) -> Set[_HashableT]:
    return set(itertools.chain(graph.keys(), *graph.values()))


def _without_optional(hint):
    if get_origin(hint) == Union:
        args = get_args(hint)
    else:
        return hint
    if len(args) != 2:
        raise ValueError
    if args[0] is None:
        return args[1]
    else:
        return args[0]


def _predecessors_list(
    funcs: Iterable[Any],
) -> Dict[Any, List[Any]]:
    """Return mapping from type (node) to all types it depends on (predecessors)"""
    result = {}
    for func in funcs:
        hints = get_type_hints(func.__call__)
        node = _without_optional(hints.pop("return"))
        if node in result:
            raise ValueError(f"More than one function is providing {node}")
        result[node] = [_without_optional(hint) for hint in hints.values()]
    for hint in list(itertools.chain.from_iterable(result.values())):
        result.setdefault(hint, [])
    return result


def _providers(funcs: Iterable[Any]) -> Dict[Any, Any]:
    """Return mapping from type (node) to the function that provides that type"""
    result = {}
    for func in funcs:
        hints = get_type_hints(func.__call__)
        node = _without_optional(hints.pop("return"))
        result[node] = func
    return result


class DAG:
    def __init__(self, funcs: Sequence[Any], on_stale_predecessor: Callable[[], Any]):
        if any(func.__call__.__defaults__ for func in funcs):
            raise ValueError("Any default arguments must be for keyword only arguments")

        self._providers = _providers(funcs)
        self._predecessors_lists = _predecessors_list(funcs)
        self._on_stale_predecessor = on_stale_predecessor
        self._nodes: Set[Any] = _nodes(self._predecessors_lists)

    @property
    def predecessors_list(self) -> _AdjacencyListT[Any]:
        return self._predecessors_lists

    def _call_func(self, func, state):
        call = func.__call__
        kwdefaults = call.__kwdefaults__ or {}

        wants = {
            name: _without_optional(hint)
            for name, hint in get_type_hints(call).items()
            if name != "return"
        }
        requires = {
            name: hint for name, hint in wants.items() if name not in kwdefaults
        }
        available = {
            name: state[hint]
            for name, hint in wants.items()
            if hint in state and state[hint] is not None
        }
        missing = set(requires) - set(available)
        if missing:
            self._on_stale_predecessor()
            return None

        return func(**available)

    def __call__(self, *objs):
        sorter = graphlib.TopologicalSorter(self._predecessors_lists)
        sorter.prepare()

        done = {type(obj): obj for obj in objs}
        for cls in sorter.get_ready():
            done.setdefault(cls, None)
            sorter.done(cls)

        while sorter.is_active():
            for cls in sorter.get_ready():
                func = self._providers[cls]
                obj = self._call_func(func, done)
                done[cls] = obj
                sorter.done(cls)

        assert set(done) == self._nodes
