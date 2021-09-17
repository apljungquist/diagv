from typing import Dict, Hashable, Iterable, Mapping, Set, TypeVar

HashableT = TypeVar("HashableT", bound=Hashable)
AdjacencyListT = Mapping[HashableT, Iterable[HashableT]]
NormalizedAdjacencyList = Dict[HashableT, Set[HashableT]]
