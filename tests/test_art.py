import textwrap

import pytest

from rappf import art


@pytest.mark.parametrize(
    "graph, expected",
    [
        (
            {
                "a": "bc",
                "b": "c",
                "c": "",
                "d": "ac",
            },
            """
            c-+---+---+
              +-b-+   |
                  +-a-+
                      +-d
            """,
        ),
        (
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
                "k": [],  # ["j"], # severing this link trashes the art
                "l": ["k"],
                "m": ["k", "l"],
                "n": ["k"],
                "o": ["m", "n"],
                "p": ["m"],
                "q": ["m"],
                "u": [],
            },
            """
            k-+---+---+
              +-l-|---+
                  +-n-|---+
                      +-m-+---+---+
                          +-o |   |
                              +-p |
                                  +-q
                                        a-+-------+
                                          +-c-+   |
                                              +-d-|---+
                                                  +-b-|-----------+
                                                      +-e-+-------|---+
                                                          +-f-----+   |
                                                                u-|---|---+
                                                                  +-g-+---+
                                                                      +-h-+
                                                                          +-i-+
                                                                              +-j
            """,
        ),
    ],
)
def test_art_looks_reasonable_by_example(graph, expected):
    # Output does not need to look exactly as in these examples
    expected = textwrap.dedent(expected)[1:-1]  # remove leading and trailing newlines
    actual = art.art(graph)
    assert actual == expected
