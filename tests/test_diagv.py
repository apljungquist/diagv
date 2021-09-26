import textwrap

import pytest

from diagv import generators, misc, optimization, visualization


def foo():
    ...


def bar():
    ...


def foobar():
    ...


@pytest.mark.parametrize(
    "graph, ordering, fmt, expected",
    [
        (
            misc.digraph({foo: [foobar], bar: [foobar]}),
            [foo, bar, foobar],
            lambda obj: obj.__name__,
            """
            foo-------+
                  bar-+
                      +-foobar
            """,
        ),
        (
            generators.dibull(),
            [0, 1, 2, 3, 4],
            str,
            """
            0-+
              +-1-+---+
                  +-2-+
                      +-3-+
                          +-4
            """,
        ),
        (
            generators.distar(4),
            [0, 1, 2, 3, 4],
            str,
            """
            0-+---+---+---+
              +-1 |   |   |
                  +-2 |   |
                      +-3 |
                          +-4
            """,
        ),
        (
            generators.distar(-4),
            [1, 2, 3, 4, 0],
            str,
            """
            1-------------+
                2---------+
                    3-----+
                        4-+
                          +-0
            """,
        ),
        (
            generators.ditutte_fragment(),
            "ACBEDGHMIFJNKLOQP",
            str,
            """
            A-+---+
              +-C-|---+-----------------------+
                  +-B-+---+                   |
                      +-E-|---------------+   |
                          +-D-+---+       |   |
                              +-G-|---+---|---|---------------+
                                  +-H-+---+   |               |
                                      +-M-|---|-------+       |
                                          +-I-|---+   |       |
                                              +-F-+---|---+   |
                                                  +-J-+   |   |
                                                      +-N-|---|---+
                                                          +-K-|---+-------+
                                                              +-L-+---+   |
                                                                  +-O |   |
                                                                      +-Q |
                                                                          +-P
            """,
        ),
        (
            misc.digraph(
                {
                    "a": [],
                    "b": ["a"],
                    "c": ["a"],
                    "d": ["c"],
                    "e": ["d"],
                    "f": ["e"],
                    "g": ["f", "b"],
                    "h": ["g", "e"],
                    "i": ["g", "u", "h"],
                    "j": ["i"],
                    "k": ["j"],
                    "l": ["k"],
                    "m": ["k", "l"],
                    "n": ["k"],
                    "o": ["m", "n"],
                    "p": ["m"],
                    "q": ["m"],
                    "u": [],
                },
                -1,
            ),
            "abcdefghuijklmnopq",
            str,
            """
            a-+---+
              +-b-|---------------+
                  +-c-+           |
                      +-d-+       |
                          +-e-+---|---+
                              +-f-+   |
                                  +-g-+-------+
                                      +-h-----+
                                            u-+
                                              +-i-+
                                                  +-j-+
                                                      +-k-+---+---+
                                                          +-l-+   |
                                                              +-m-|---+---+---+
                                                                  +-n-+   |   |
                                                                      +-o |   |
                                                                          +-p |
                                                                              +-q
            """,
        ),
        (
            generators.a_ring(),
            "ABCDEFGHI",
            str,
            """
            +-A-+-----------+
            |   +-B         |
            |       +-C-----|-------+
            |       |     D-+       |
            |       |       +-E-----|-------+
            |       |       +-----F |       |
            +-------|---------------+-G     |
                    |                   +-H |
                    +-------------------+---+-I
            """,
        ),
        (
            generators.a_ring(),
            "DFEIHCGAB",
            str,
            """
            D-----+
                F-+
                  +-E-+
                  |   +-I-+---+
                  |       +-H |
                  |           +-C-+
                  |               +-G-+
                  +-------------------+-A-+
                                          +-B
            """,
        ),
    ],
)
def test_drawing_by_example(graph, ordering, fmt, expected):
    # Output does not need to look exactly as in these examples
    expected = textwrap.dedent(expected)[1:-1]  # remove leading and trailing newlines
    actual = visualization.text_art(
        graph,
        ordering=ordering,
        fmt=fmt,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "graph, expected",
    [
        (
            misc.digraph({foo: [foobar], bar: [foobar]}),
            [foo, bar, foobar],
        ),
        (
            generators.dibull(),
            [0, 1, 2, 3, 4],
        ),
        (
            generators.distar(4),
            [0, 1, 2, 3, 4],
        ),
        (
            generators.distar(-4),
            [1, 2, 3, 4, 0],
        ),
        (
            generators.ditutte_fragment(),
            "ACBEDGHMIFJNKLOQP",
        ),
        (
            misc.digraph(
                {
                    "a": [],
                    "b": ["a"],
                    "c": ["a"],
                    "d": ["c"],
                    "e": ["d"],
                    "f": ["e"],
                    "g": ["f", "b"],
                    "h": ["g", "e"],
                    "i": ["g", "u", "h"],
                    "j": ["i"],
                    "k": ["j"],
                    "l": ["k"],
                    "m": ["k", "l"],
                    "n": ["k"],
                    "o": ["m", "n"],
                    "p": ["m"],
                    "q": ["m"],
                    "u": [],
                },
                -1,
            ),
            "abcdefghuijklmnopq",
        ),
    ],
)
def test_optimization_by_example(graph, expected):
    # Output does not need to look exactly as in these examples
    assert list(optimization.sorted_topological(graph)) == list(expected)
