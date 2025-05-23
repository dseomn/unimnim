# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
import re

import pytest

from unimnim import data
from unimnim import input_method


@pytest.mark.parametrize(
    "sequence,expected_language",
    (
        ("a", "en"),  # From ES_STANDARD.
        ("A", "en"),  # Needs icu.USET_ADD_CASE_MAPPINGS to get uppper case.
        ("\N{LATIN SMALL LETTER I WITH DIAERESIS}", "en"),  # From ES_AUXILIARY.
        ("!", "en"),  # From ES_PUNCTUATION.
        ("0", "en"),  # From the numbering system.
        (
            (
                "\N{REGIONAL INDICATOR SYMBOL LETTER U}"
                "\N{REGIONAL INDICATOR SYMBOL LETTER N}"
            ),
            "emoji",
        ),
        ("\N{DOUBLE EXCLAMATION MARK}\ufe0e", "text-presentation"),
    ),
)
def test_known_sequences_present_with_language(
    sequence: str, expected_language: str
) -> None:
    assert expected_language in input_method.known_sequences()[sequence]


@pytest.mark.parametrize(
    "sequence",
    (
        # NFC of a single code point.
        "\N{HEBREW LETTER BET}\N{HEBREW POINT DAGESH OR MAPIQ}",
    ),
)
def test_known_sequences_present_without_languages(sequence: str) -> None:
    # To find other test cases if any of these are added to exemplar data:
    #
    # jq 'to_entries | .[] | select(.value == []) | .key' \
    #   < output/known_sequences.json
    assert not input_method.known_sequences()[sequence]


@pytest.mark.parametrize(
    "groups,error_regex",
    (
        (
            {
                "latin": data.Group(
                    prefix="l",
                    base={"n": "n"},
                    combining=data.Combining(
                        name_regex_replace={
                            "'": (
                                (
                                    re.compile(r".*"),
                                    r"\g<0> PRECEDED BY APOSTROPHE",
                                ),
                            ),
                        },
                    ),
                ),
            },
            r"Mnemonic \"ln'\" has result .* with discouraged sequences",
        ),
        (
            {
                "latin": data.Group(
                    prefix="l",
                    base={"a": "a", "a'": "b"},
                    combining=data.Combining(
                        append={"'": "\N{COMBINING ACUTE ACCENT}"},
                    ),
                ),
            },
            "Group 'latin' has duplicate",
        ),
        (
            {
                "latin1": data.Group(
                    prefix="l",
                    base={"a": "a"},
                ),
                "latin2": data.Group(
                    prefix="l",
                    base={"a": "a"},
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
                    combining=data.Combining(
                        append={
                            "*": "\N{COMBINING DOT ABOVE}",
                            ".": "\N{COMBINING DOT BELOW}",
                        },
                    ),
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
                    combining=data.Combining(
                        append={",": "\N{COMBINING CEDILLA}"},
                    ),
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
                    combining=data.Combining(
                        append={
                            "~": "\N{COMBINING TILDE}",
                            ".": "\N{COMBINING DOT ABOVE}",
                        },
                    ),
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
            # combining.name_regex_replace works and can stack with
            # combining.append.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"o": "o"},
                    combining=data.Combining(
                        append={"'": "\N{COMBINING ACUTE ACCENT}"},
                        name_regex_replace={
                            "/": ((re.compile(r".*"), r"\g<0> WITH STROKE"),),
                        },
                    ),
                ),
            },
            {
                "lo": "o",
                "lo'": "\N{LATIN SMALL LETTER O WITH ACUTE}",
                "lo/": "\N{LATIN SMALL LETTER O WITH STROKE}",
                "lo/'": "\N{LATIN SMALL LETTER O WITH STROKE AND ACUTE}",
            },
        ),
        (
            # A combining.name_regex_replace entry can have multiple replacement
            # rules.
            {
                "latin": data.Group(
                    prefix="l",
                    base={
                        "O": "O",
                        "o": "o",
                    },
                    combining=data.Combining(
                        name_regex_replace={
                            "/": (
                                (
                                    re.compile(r"LATIN CAPITAL LETTER .*"),
                                    r"\g<0> WITH STROKE",
                                ),
                                (
                                    re.compile(r"LATIN SMALL LETTER .*"),
                                    r"\g<0> WITH STROKE",
                                ),
                            ),
                        },
                    ),
                ),
            },
            {
                "lO": "O",
                "lO/": "\N{LATIN CAPITAL LETTER O WITH STROKE}",
                "lo": "o",
                "lo/": "\N{LATIN SMALL LETTER O WITH STROKE}",
            },
        ),
        (
            # combining.name_regex_replace ignores incorrect names, but can
            # match corrected names.
            {
                "math": data.Group(
                    prefix="m",
                    base={
                        "B": "B",
                        "P": "P",
                        "W": "W",
                    },
                    combining=data.Combining(
                        name_regex_replace={
                            "F": (
                                (
                                    re.compile(r"LATIN CAPITAL LETTER (.*)"),
                                    r"\g<1>EIERSTRASS ELLIPTIC FUNCTION",
                                ),
                            ),
                            "S": (
                                (
                                    re.compile(r"LATIN CAPITAL LETTER (.*)"),
                                    r"SCRIPT CAPITAL \g<1>",
                                ),
                            ),
                            "f": (
                                (
                                    re.compile(
                                        r"(.*)EIERSTRASS ELLIPTIC FUNCTION"
                                    ),
                                    r"LATIN SMALL LETTER \g<1>",
                                ),
                            ),
                            "s": (
                                (
                                    re.compile(r"SCRIPT CAPITAL (.*)"),
                                    r"LATIN SMALL LETTER \g<1>",
                                ),
                            ),
                        },
                    ),
                ),
            },
            {
                "mB": "B",
                "mBS": "\N{SCRIPT CAPITAL B}",
                "mBSs": "b",
                "mP": "P",
                # U+2118 SCRIPT CAPITAL P has a corrected name, WEIERSTRASS
                # ELLIPTIC FUNCTION, so mPS does not match.
                "mW": "W",
                "mWF": "\N{SCRIPT CAPITAL P}",  # But the correction does match.
                # No "mWFs" because "SCRIPT CAPITAL P" is not checked against
                # the regexes.
                "mWFf": "w",  # But the correction is checked.
            },
        ),
        (
            # A regex that does not match is not an error.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"o": "o"},
                    combining=data.Combining(
                        name_regex_replace={
                            "/": (
                                (
                                    re.compile(r"no match"),
                                    r"\g<0> WITH STROKE",
                                ),
                            ),
                        },
                    ),
                ),
            },
            {"lo": "o"},
        ),
        (
            # A regex that produces a name that does not exist is not an error.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"o": "o"},
                    combining=data.Combining(
                        name_regex_replace={
                            "/": (
                                (
                                    re.compile(r".*"),
                                    r"\g<0> WITH A FAKE ACCENT",
                                ),
                            ),
                        },
                    ),
                ),
            },
            {"lo": "o"},
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
                    combining=data.Combining(
                        append={"'": "\N{COMBINING ACUTE ACCENT}"},
                    ),
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
                    combining=data.Combining(
                        append={
                            ".": "\N{COMBINING DOT ABOVE}",
                            "..": "\N{COMBINING DOT BELOW}",
                        },
                    ),
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
                    combining=data.Combining(
                        append={"~": "\N{COMBINING GREEK PERISPOMENI}"},
                    ),
                ),
                "latin": data.Group(
                    prefix="l",
                    base={"a": "a"},
                    combining=data.Combining(
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
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
            # Empty results are filtered out before checking for conflicts
            # between groups.
            {
                "latin1": data.Group(
                    prefix="l",
                    base={"a": "a"},
                ),
                "latin2": data.Group(
                    prefix="la",
                    base={"": ""},
                    combining=data.Combining(
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
                ),
            },
            {
                "la": "a",
                "la~": "\N{COMBINING TILDE}",
            },
        ),
        (
            # A base mnemonic can have an empty result to allow typing combining
            # characters.
            {
                "latin": data.Group(
                    prefix="l",
                    base={"_": ""},
                    combining=data.Combining(
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
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
                    combining=data.Combining(
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
                ),
            },
            {"l~": "\N{COMBINING TILDE}"},
        ),
        (
            # Combining characters can stack over an empty base result.
            {
                "regions": data.Group(
                    prefix="r",
                    base={"": ""},
                    combining=data.Combining(
                        append={
                            "N": "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
                            "U": "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
                        },
                    ),
                ),
            },
            {
                "rN": "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
                "rU": "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
                "rNU": (
                    "\N{REGIONAL INDICATOR SYMBOL LETTER N}"
                    "\N{REGIONAL INDICATOR SYMBOL LETTER U}"
                ),
                "rUN": (
                    "\N{REGIONAL INDICATOR SYMBOL LETTER U}"
                    "\N{REGIONAL INDICATOR SYMBOL LETTER N}"
                ),
            },
        ),
    ),
)
def test_generate_map(
    groups: Mapping[str, data.Group],
    expected: Mapping[str, str],
) -> None:
    assert input_method.generate_map(groups) == expected


@pytest.mark.parametrize(
    "map_,expected",
    (
        (
            {
                "a": "A",
                "abc": "ABC",
                "b": "B",
            },
            {
                "": ["A", "ABC", "B"],
                "a": ["A", "ABC"],
                "ab": ["ABC"],
                "abc": ["ABC"],
                "b": ["B"],
            },
        ),
        (
            {
                "abc": "A",
                "acb": "A",
            },
            {
                "": ["A"],  # no duplicates despite multiple mnemonics for A
                "a": ["A"],  # ditto
                "ab": ["A"],
                "abc": ["A"],
                "ac": ["A"],
                "acb": ["A"],
            },
        ),
    ),
)
def test_generate_prefix_map(
    map_: Mapping[str, str], expected: Mapping[str, Sequence[str]]
) -> None:
    assert input_method.generate_prefix_map(map_) == expected


@pytest.mark.parametrize(
    "s,expected",
    (
        ('"', r'"\""'),
        ("\\", r'"\\"'),
        ("f00 b@r", '"f00 b@r"'),
        ("\x00\x11", r'"\u0 \u11 "'),
        ("\x00\N{CANCEL TAG}", '"\\u0 \N{CANCEL TAG}"'),
    ),
)
def test_m17n_mtext(s: str, expected: str) -> None:
    assert input_method.m17n_mtext(s) == expected


def test_render_template() -> None:
    assert input_method.render_template(r"{{ x | m17n_mtext }}", x="a") == '"a"'
