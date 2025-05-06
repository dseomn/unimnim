# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping

import pytest

from unimnim import data
from unimnim import input_method


def test_known_sequences() -> None:
    known_sequences = input_method.known_sequences()

    # From ES_STANDARD.
    assert "en" in known_sequences["a"]

    # Needs icu.USET_ADD_CASE_MAPPINGS to get uppper case.
    assert "en" in known_sequences["A"]

    # From ES_AUXILIARY.
    assert "en" in known_sequences["\N{LATIN SMALL LETTER I WITH DIAERESIS}"]

    # From ES_PUNCTUATION.
    assert "en" in known_sequences["!"]


@pytest.mark.parametrize(
    "groups,error_regex",
    (
        (
            {
                "latin": data.Group(
                    prefix="l",
                    base={"a": "a", "a'": "b"},
                    combining={"'": "\N{COMBINING ACUTE ACCENT}"},
                ),
            },
            "Group 'latin' has duplicate",
        ),
        (
            {
                "latin1": data.Group(
                    prefix="l",
                    base={"a": "a"},
                    combining={},
                ),
                "latin2": data.Group(
                    prefix="l",
                    base={"a": "a"},
                    combining={},
                ),
            },
            "groups have the same mnemonics",
        ),
    ),
)
def test_generate_map_error(
    groups: Mapping[str, data.Group],
    error_regex: str,
) -> None:
    with pytest.raises(ValueError, match=error_regex):
        input_method.generate_map(groups)


@pytest.mark.parametrize(
    "groups,expected",
    (
        (
            # Combining characters can stack, in any valid order.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"s": "s"},
                    combining={
                        "*": "\N{COMBINING DOT ABOVE}",
                        ".": "\N{COMBINING DOT BELOW}",
                    },
                ),
            },
            {
                "ls": "s",
                "ls*": "\N{LATIN SMALL LETTER S WITH DOT ABOVE}",
                "ls.": "\N{LATIN SMALL LETTER S WITH DOT BELOW}",
                "ls*.": "\N{LATIN SMALL LETTER S WITH DOT BELOW AND DOT ABOVE}",
                "ls.*": "\N{LATIN SMALL LETTER S WITH DOT BELOW AND DOT ABOVE}",
            },
        ),
        (
            # Known sequences of length > 1 can be produced.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"a": "a"},
                    combining={",": "\N{COMBINING CEDILLA}"},
                ),
            },
            {
                "la": "a",
                "la,": "a\N{COMBINING CEDILLA}",
            },
        ),
        (
            # Known sequences of length > 2 can be produced even if they start
            # with a sequence that cannot be produced.
            #
            # This test case was found by loading the known_sequences.json file
            # and running:
            #
            # [
            #   (x, list(map(unicodedata.name, x)))
            #   for x in known_sequences
            #   if len(x) > 2 and x[:-1] not in known_sequences
            # ]
            {
                "latin": data.Group(
                    prefix="l",
                    base={"j": "j"},
                    combining={
                        "~": "\N{COMBINING TILDE}",
                        ".": "\N{COMBINING DOT ABOVE}",
                    },
                ),
            },
            {
                "lj": "j",
                "lj~": "j\N{COMBINING TILDE}",
                # Note that "lj." is not present.
                "lj.~": "j\N{COMBINING DOT ABOVE}\N{COMBINING TILDE}",
            },
        ),
        (
            # Base mnemonics can overlap.
            {
                "latin": data.Group(
                    prefix="l",
                    base={
                        "a": "a",
                        "ae": "\N{LATIN SMALL LETTER AE}",
                    },
                    combining={"'": "\N{COMBINING ACUTE ACCENT}"},
                ),
            },
            {
                "la": "a",
                "la'": "\N{LATIN SMALL LETTER A WITH ACUTE}",
                "lae": "\N{LATIN SMALL LETTER AE}",
                "lae'": "\N{LATIN SMALL LETTER AE WITH ACUTE}",
            },
        ),
        (
            # Combining mnemonics can overlap. Overlapping combining mnemonics
            # can even stack together, as long as the order isn't important.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"s": "s"},
                    combining={
                        ".": "\N{COMBINING DOT ABOVE}",
                        "..": "\N{COMBINING DOT BELOW}",
                    },
                ),
            },
            {
                "ls": "s",
                "ls.": "\N{LATIN SMALL LETTER S WITH DOT ABOVE}",
                "ls..": "\N{LATIN SMALL LETTER S WITH DOT BELOW}",
                "ls...": (
                    "\N{LATIN SMALL LETTER S WITH DOT BELOW AND DOT ABOVE}"
                ),
            },
        ),
        (
            # Different groups can give different meanings to the same
            # mnemonics.
            {
                "greek": data.Group(
                    prefix="g",
                    base={"a": "\N{GREEK SMALL LETTER ALPHA}"},
                    combining={"~": "\N{COMBINING GREEK PERISPOMENI}"},
                ),
                "latin": data.Group(
                    prefix="l",
                    base={"a": "a"},
                    combining={"~": "\N{COMBINING TILDE}"},
                ),
            },
            {
                "ga": "\N{GREEK SMALL LETTER ALPHA}",
                "ga~": "\N{GREEK SMALL LETTER ALPHA WITH PERISPOMENI}",
                "la": "a",
                "la~": "\N{LATIN SMALL LETTER A WITH TILDE}",
            },
        ),
        (
            # A base mnemonic can have an empty result to allow typing combining
            # characters.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"_": ""},
                    combining={"~": "\N{COMBINING TILDE}"},
                ),
            },
            {"l_~": "\N{COMBINING TILDE}"},
        ),
        (
            # A base mnemonic can itself be empty to allow typing combining
            # characters without any additional prefix.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"": ""},
                    combining={"~": "\N{COMBINING TILDE}"},
                ),
            },
            {"l~": "\N{COMBINING TILDE}"},
        ),
    ),
)
def test_generate_map(
    groups: Mapping[str, data.Group],
    expected: Mapping[str, str],
) -> None:
    assert input_method.generate_map(groups) == expected


def test_generate_prefix_map() -> None:
    assert input_method.generate_prefix_map(
        {
            "a": "A",
            "abc": "ABC",
            "b": "B",
        }
    ) == {
        "": ["A", "ABC", "B"],
        "a": ["A", "ABC"],
        "ab": ["ABC"],
        "abc": ["ABC"],
        "b": ["B"],
    }


@pytest.mark.parametrize(
    "s,expected",
    (
        ('"', r'"\""'),
        ("\\", r'"\\"'),
        ("f00 b@r", '"f00 b@r"'),
        ("\x00\x11", r'"\u0 \u11 "'),
    ),
)
def test_m17n_mtext(s: str, expected: str) -> None:
    assert input_method.m17n_mtext(s) == expected


def test_render_template() -> None:
    assert input_method.render_template(r"{{ x | m17n_mtext }}", x="a") == '"a"'
