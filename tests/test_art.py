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
            a-+---+
              +-b-|-------------------------------------------+
                  +-c-----------------------------+           |
                        k-+---+---+               |           |
                          +-l-|---+               |           |
                              +-n-|---+           |           |
                                  +-m-+---+---+   |           |
                                      +-o |   |   |           |
                                          +-q |   |           |
                                              +-p |           |
                                                  +-d-+       |
                                                      +-e-+---|---+
                                                          +-f-+   |
                                                              +-g-+-------+
                                                                  +-h-----+
                                                                        u-+
                                                                          +-i-+
                                                                              +-j
            """,
        ),
        (
            {"a2": ["a1"], "a3": ["a2"], "b2": ["b1"], "b3": ["b2"], "c": ["a3", "b3"]},
            """
        a1-+
           +-a2-+
                +-a3----------------+
                       b1-+         |
                          +-b2-+    |
                               +-b3-+
                                    +-c
        """,
        ),
    ],
)
def test_art_looks_reasonable_by_example(graph, expected):
    # Output does not need to look exactly as in these examples
    expected = textwrap.dedent(expected)[1:-1]  # remove leading and trailing newlines
    actual = art.art(graph)
    assert actual == expected
