#!/usr/bin/env python3
import dataclasses
from typing import Optional, get_type_hints

import fire

from rappf import art, dag


@dataclasses.dataclass
class Time:
    v: str


@dataclasses.dataclass
class Message:
    v: str


@dataclasses.dataclass
class MarkAllRead:
    ...


@dataclasses.dataclass
class NumUnread:
    v: int


@dataclasses.dataclass
class MostRecent:
    v: str


@dataclasses.dataclass
class Greeting:
    v: str


class NumUnread0:
    def __init__(self):
        self._num_unread = 0

    def __call__(
        self, *, message: Optional[Message] = None, reset: Optional[MarkAllRead] = None
    ) -> NumUnread:
        if message is not None:
            self._num_unread += 1
        if reset is not None:
            self._num_unread = 0
        return NumUnread(self._num_unread)


class MostRecent0:
    def __init__(self):
        self._most_recent = None

    def __call__(self, *, message: Optional[Message] = None) -> Optional[MostRecent]:
        if message is not None:
            self._most_recent = message.v
        if self._most_recent is None:
            return None
        return MostRecent(self._most_recent)


class Greeting0:
    def __init__(self, name: str):
        self._name = name

    def __call__(
        self, *, when: Time, most_recent: MostRecent, num_unread: NumUnread
    ) -> Greeting:
        lines = [
            f"Hello {self._name}.",
            f"It is {when.v} o'clock.",
            f"You have {num_unread.v} unread message(s).",
        ]
        if most_recent is not None:
            lines.append(f"Your most recent message is: '{most_recent.v}'.")
        return Greeting("\n".join(lines))


def _dict_zip(left, right):
    keys = left.keys() & right.keys()
    for key in keys:
        yield key, left[key], right[key]


class Debugger:
    def __call__(
        self,
        *,
        when: Optional[Time] = None,
        current: Optional[Message] = None,
        most_recent: Optional[MostRecent] = None,
        reset: Optional[MarkAllRead] = None,
        num_unread: Optional[NumUnread] = None,
        greeting: Optional[Greeting] = None,
    ) -> None:
        for name, hint, value in _dict_zip(get_type_hints(self.__call__), locals()):
            print(f"{name}: {hint} = {value}")


def _engine(debugger):
    funcs = [NumUnread0(), MostRecent0(), Greeting0("Alice")]
    if debugger is not None:
        funcs.append(debugger)
    return dag.DAG(funcs, lambda: None)


def run():
    engine = _engine(Debugger())
    updates = [
        [
            Time("09.00"),
            Message("Hej"),
            MarkAllRead(),
        ],
        [Time("10:00")],
        [
            Time("11.00"),
            Message("Guten tag"),
        ],
        [
            Time("12.00"),
            Message("Hola"),
        ],
        [
            MarkAllRead(),
        ],
        [
            Time("13.00"),
            Message("Bonjour"),
        ],
    ]

    for update in updates:
        print("=" * 88)
        print(update)
        print()
        engine(*update)


def visualize():
    engine = _engine(None)
    return art.art(
        engine.predecessors_list, max_col_width=None, fmt=lambda cls: cls.__name__
    )


if __name__ == "__main__":
    fire.Fire({func.__name__: func for func in [visualize, run]})
