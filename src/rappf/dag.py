"""Functionality to play, record and replay the app dag

Models app as a directed acyclic graph (DAG) in which
* data types are the nodes, and
* functions are the edges, each function can represent one or more edges.
"""
import contextlib
import graphlib
import itertools
import json
import logging
import pathlib
from typing import (
    Any,
    Callable,
    Dict,
    Hashable,
    Iterable,
    List,
    Mapping,
    Optional,
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

logger = logging.getLogger(__name__)

_T = TypeVar("_T")
_HashableT = TypeVar("_HashableT", bound=Hashable)
_AdjacencyListT = Mapping[_HashableT, Iterable[_HashableT]]

_JsonObjectT = Dict[str, Any]
_JsonListT = List[Any]
_JsonSimpleT = Union[bool, float, int, None, str]
JsonAnyT = Union[_JsonObjectT, _JsonListT, _JsonSimpleT]


class _SupportsToJsonP(Protocol):
    def to_json(self) -> JsonAnyT:
        ...


class _SupportsFromJsonP(Protocol):
    @classmethod
    def from_json(cls: Type[_T], obj: JsonAnyT) -> _T:
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
    def __init__(
        self,
        funcs: Sequence[Any],
        on_stale_predecessor: Callable[[], Any],
        expected_sources: Optional[Iterable[Any]] = None,
    ):
        if any(func.__call__.__defaults__ for func in funcs):
            raise ValueError("Any default arguments must be for keyword only arguments")

        self._providers = _providers(funcs)
        self._predecessors_lists = _predecessors_list(funcs)
        self._on_stale_predecessor = on_stale_predecessor
        self._nodes: Set[Any] = _nodes(self._predecessors_lists)

        # Help users sanity check their configuration
        if expected_sources is not None:
            expected_sources = set(expected_sources)
            actual_sources = set(
                node for node in self._nodes if not self._providers.get(node, [])
            )
            if actual_sources != expected_sources:
                extra = actual_sources - expected_sources
                missing = expected_sources - actual_sources
                if extra:
                    logger.debug("Unexpected sources found: %s", extra)
                if missing:
                    logger.debug("Expected sources not found: %s", missing)
                raise ValueError("Actual sources do not match expected sources")

    @property
    def predecessors_list(self) -> _AdjacencyListT[Any]:
        return self._predecessors_lists

    def _update_node(self, func, state):
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

    def _update_graph(self, objs):
        sorter = graphlib.TopologicalSorter(self._predecessors_lists)
        sorter.prepare()

        done = {cls: obj for cls, obj in objs.items()}
        for cls in sorter.get_ready():
            done.setdefault(cls, None)
            sorter.done(cls)

        while sorter.is_active():
            for cls in sorter.get_ready():
                if cls not in done:
                    func = self._providers[cls]
                    obj = self._update_node(func, done)
                    done[cls] = obj
                sorter.done(cls)

        assert set(done) == self._nodes
        return done

    def run(
        self,
        updates: Optional[Iterable[Any]] = None,
        replay: Iterable[Type[_SupportsFromJsonP]] = (),
        capture: Iterable[Type[_SupportsToJsonP]] = (),
        no_cut_ok: bool = False,
        location: Optional[pathlib.Path] = None,
    ) -> None:
        """Run the DAG

        :param updates: Updates to be applied, not from cache.
        :param capture: Nodes to write to cache.
        :param replay: Nodes to read from cache.
        :param no_cut_ok: If False, raise an error if either capture or replay is set
            and do not cause a cut.
        """
        if (capture or replay) and no_cut_ok is False:
            raise NotImplementedError

        if (capture or replay) and location is None:
            raise ValueError("Must provide a location for capture and/or replay")

        if capture and replay:
            raise NotImplementedError

        if replay and updates:
            raise NotImplementedError

        with contextlib.ExitStack() as stack:
            if capture:
                assert location is not None
                writer = stack.enter_context(_Writer(capture, location))
            else:
                writer = None

            if replay:
                assert updates is None
                assert location is not None
                seeds = stack.enter_context(_Reader(replay, location))
            else:
                assert updates is not None
                seeds = ({type(obj): obj for obj in update} for update in updates)

            for seed in seeds:
                state = self._update_graph(seed)
                writer and writer(state)


class _Writer:
    def __init__(
        self, nodes: Iterable[Type[_SupportsToJsonP]], location: pathlib.Path
    ) -> None:
        self._location = location
        self._nodes = list(nodes)
        self._files = {}  # type: ignore

    def __enter__(self):
        for node in self._nodes:
            reg_path = (self._location / node.__name__).with_suffix(".jsonl")
            self._files[node] = reg_path.open("x")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for file in self._files.values():
            file.close()

    def __call__(
        self, state: Mapping[Type[_SupportsToJsonP], _SupportsToJsonP]
    ) -> None:
        for node in self._nodes:
            obj = state[node]
            file = self._files[node]
            file.write(json.dumps(None if obj is None else obj.to_json()))
            file.write("\n")


def _maybe_from_json(
    cls: Type[_SupportsFromJsonP], jsn: JsonAnyT
) -> Optional[_SupportsFromJsonP]:
    if jsn is None:
        return None
    return cls.from_json(jsn)


class _Reader:
    def __init__(
        self, nodes: Iterable[Type[_SupportsFromJsonP]], location: pathlib.Path
    ) -> None:
        self._location = location
        self._nodes = list(nodes)
        self._files = {}  # type: ignore

    def __enter__(self):
        for node in self._nodes:
            reg_path = (self._location / node.__name__).with_suffix(".jsonl")
            self._files[node] = reg_path.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for file in self._files.values():
            file.close()

    def __iter__(self):
        return self

    def __next__(self):
        lines = {node: self._files[node].readline() for node in self._nodes}
        if not all(lines.values()):
            raise StopIteration
        return {
            node: _maybe_from_json(node, json.loads(line))
            for node, line in lines.items()
        }
