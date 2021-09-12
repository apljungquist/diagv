#!/usr/bin/env python3
"""A simple app that counts unread messages.

When visualized its DAG looks something like

Message----------------------+------------+
          MarkAllRead--------|------------+
                        Time-|------------|-----------+
                             +-MostRecent-|-----------+
                                          +-NumUnread-+
                                                      +-Greeting
"""
import dataclasses
import datetime
import logging
import os
import pathlib
from typing import Optional, Type, TypeVar, Union, get_type_hints

import fire

from rappf import art, dag

_T = TypeVar("_T")


@dataclasses.dataclass
class JsonMixin:
    @classmethod
    def from_json(cls: Type[_T], obj: dag.JsonAnyT) -> _T:
        return cls(**obj)  # type: ignore

    def to_json(self) -> dag.JsonAnyT:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Time(JsonMixin):
    v: str


@dataclasses.dataclass
class Message(JsonMixin):
    v: str


@dataclasses.dataclass
class MarkAllRead(JsonMixin):
    ...


@dataclasses.dataclass
class NumUnread(JsonMixin):
    v: int


@dataclasses.dataclass
class MostRecent(JsonMixin):
    v: str


@dataclasses.dataclass
class Greeting(JsonMixin):
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
    def __init__(self):
        self.greetings = []

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
        self.greetings.append(greeting)
        print("=" * 88)
        for name, hint, value in _dict_zip(get_type_hints(self.__call__), locals()):
            print(f"{name}: {hint} = {value}")


def _engine(debugger):
    funcs = [NumUnread0(), MostRecent0(), Greeting0("Alice")]
    if debugger is not None:
        funcs.append(debugger)
    return dag.DAG(funcs, lambda: None, expected_sources=[Time, Message, MarkAllRead])


def run(location: Union[None, str, pathlib.Path] = None) -> None:
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
    if location is None:
        location = pathlib.Path().cwd() / datetime.datetime.now().strftime(
            "%Y%m%d_%HM%s"
        )
    else:
        location = pathlib.Path(location)

    location.mkdir()
    debuggers = [Debugger() for _ in range(3)]
    _engine(debuggers[0]).run(updates)
    _engine(debuggers[1]).run(
        updates,
        capture=[Time, MostRecent, NumUnread],
        no_cut_ok=True,
        location=location,
    )
    _engine(debuggers[2]).run(
        replay=[Time, MostRecent, NumUnread],
        no_cut_ok=True,
        location=location,
    )
    # The sinks (indeed all nodes downsteam of A cut) should see the same states
    # regardless of how the app is run.
    assert debuggers[0].greetings == debuggers[1].greetings == debuggers[2].greetings


def visualize():
    engine = _engine(None)
    return art.art(
        engine.predecessors_list, max_col_width=None, fmt=lambda cls: cls.__name__
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging._nameToLevel[os.environ.get("LEVEL", "WARNING")])
    fire.Fire({func.__name__: func for func in [visualize, run]})
