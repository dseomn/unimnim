# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
import re

import pytest

from unimnim import data
from unimnim import input_method


@pytest.mark.parametrize(
    "s,expected",
    (
        ("", []),
        ("a", ["a"]),
        ("ab", ["a", "b"]),
        (
            "\N{LATIN SMALL LETTER A WITH ACUTE}",
            ["\N{LATIN SMALL LETTER A WITH ACUTE}"],
        ),
        ("a\N{COMBINING ACUTE ACCENT}", ["a\N{COMBINING ACUTE ACCENT}"]),
        (
            (
                "\N{REGIONAL INDICATOR SYMBOL LETTER U}"
                "\N{REGIONAL INDICATOR SYMBOL LETTER N}"
            ),
            [
                (
                    "\N{REGIONAL INDICATOR SYMBOL LETTER U}"
                    "\N{REGIONAL INDICATOR SYMBOL LETTER N}"
                ),
            ],
        ),
    ),
)
def test_extended_grapheme_clusters(s: str, expected: Sequence[str]) -> None:
    assert list(input_method._extended_grapheme_clusters(s)) == list(expected)


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
        "\x00",  # Single code point in no languages.
        # NFC of a single code point, missing from exemplar data.
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
    "sequence",
    (
        "\ue000",  # private use
        "\ud800",  # surrogate
        "\N{LATIN SMALL LETTER N PRECEDED BY APOSTROPHE}",  # deprecated
        "ij",  # should be split into "i" and "j"
    ),
)
def test_known_sequences_absent(sequence: str) -> None:
    assert sequence not in input_method.known_sequences()


@pytest.mark.parametrize(
    "known_1,known_2,expected_known",
    (
        (False, False, {}),
        (False, True, {"a": "b"}),
        (True, False, {"a": "b"}),
        (True, True, {"a": "b"}),
    ),
)
def test_map_duplicate_mnemonic_same_result(
    known_1: bool,
    known_2: bool,
    expected_known: Mapping[str, str],
) -> None:
    map_ = input_method._Map(group_id="kumquat")
    map_.add("a", "b", is_known=known_1)
    map_.add("a", "b", is_known=known_2)
    assert map_.known == expected_known


@pytest.mark.parametrize(
    "groups,error_regex",
    (
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    expressions=dict(main=["name_maps", "main"]),
                ),
            },
            r"Group 'latin' does not have name_map 'main'",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    name_maps=dict(main={}),
                    expressions=dict(main=["union"]),
                ),
            },
            r"Group 'latin' defines but does not use name_map",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    expressions=dict(main=["map", "main"]),
                ),
            },
            r"Group 'latin' does not have map 'main'",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={}),
                    expressions=dict(main=["union"]),
                ),
            },
            r"Group 'latin' defines but does not use map",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    name_regex_replace_maps={},
                    expressions=dict(
                        main=[
                            "combine",
                            ["union"],
                            ["name_regex_replace", "main"],
                        ],
                    ),
                ),
            },
            r"Group 'latin' does not have name_regex_replace_map 'main'",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    name_regex_replace_maps=dict(main={}),
                    expressions=dict(main=["union"]),
                ),
            },
            r"Group 'latin' defines but does not use name_regex_replace",
        ),
        (
            {
                "latin": data.Group(name="", prefix="l", expressions={}),
            },
            r"Group 'latin' does not have expression 'main'",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    expressions=dict(main=["expression", "other"]),
                ),
            },
            r"Group 'latin' does not have expression 'other'",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    expressions=dict(
                        main=["union"],
                        other=["union"],
                    ),
                ),
            },
            r"Group 'latin' defines but does not use expression",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    expressions=dict(main=["not valid at all"]),
                ),
            },
            r"Group 'latin' has invalid expression",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    expressions=dict(main=["combine", ["union"], "not valid"]),
                ),
            },
            r"Group 'latin' has invalid 'combine' option",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={"n": "n"}),
                    name_regex_replace_maps=dict(
                        main={
                            "'": (
                                (
                                    re.compile(r".*"),
                                    r"\g<0> PRECEDED BY APOSTROPHE",
                                ),
                            ),
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["name_regex_replace", "main"],
                        ],
                    ),
                ),
            },
            r"Mnemonic \"n'\" has result .* with discouraged sequences",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        one={"a": "a"},
                        two={"a": "b"},
                    ),
                    expressions=dict(
                        main=["union", ["map", "one"], ["map", "two"]],
                    ),
                ),
            },
            "Group 'latin' has duplicate",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    examples={"a": "a"},
                    maps=dict(main={}),
                    expressions=dict(main=["map", "main"]),
                ),
            },
            "Group 'latin' has example 'a' that does not exist",
        ),
        (
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    examples={"a": "a"},
                    maps=dict(main={"a": "b"}),
                    expressions=dict(main=["map", "main"]),
                ),
            },
            "Group 'latin' has example 'a' that should map to",
        ),
        (
            {
                "latin1": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={"a": "a"}),
                    expressions=dict(main=["map", "main"]),
                ),
                "latin2": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={"a": "a"}),
                    expressions=dict(main=["map", "main"]),
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
            # "name_maps" produces the cartesian product of the name parts,
            # ignoring names that don't exist.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    name_maps=dict(
                        prefixes={
                            "C": "LATIN CAPITAL LETTER ",
                            "s": "LATIN SMALL LETTER ",
                        },
                        letters={
                            "a": "A",
                            "b": "B",
                        },
                        suffixes={
                            "": "",
                            "e": "E",
                        },
                    ),
                    expressions=dict(
                        main=["name_maps", "prefixes", "letters", "suffixes"],
                    ),
                ),
            },
            {
                "lCa": "A",
                "lCae": "\N{LATIN CAPITAL LETTER AE}",
                "lCb": "B",
                "lsa": "a",
                "lsae": "\N{LATIN SMALL LETTER AE}",
                "lsb": "b",
            },
        ),
        (
            # "map" references a map.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={"a": "a"}),
                    expressions=dict(main=["map", "main"]),
                ),
            },
            {"la": "a"},
        ),
        (
            # Unknown sequences can be produced if they're explicitly in a map.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={
                            "a": (
                                "a\N{HEBREW POINT DAGESH OR MAPIQ}"
                                "\N{ARABIC MADDAH ABOVE}"
                            ),
                        },
                    ),
                    expressions=dict(main=["map", "main"]),
                ),
            },
            {
                "la": (
                    "a\N{HEBREW POINT DAGESH OR MAPIQ}\N{ARABIC MADDAH ABOVE}"
                ),
            },
        ),
        (
            # "expression" references an expression.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={"a": "a"}),
                    expressions=dict(
                        other=["map", "main"],
                        main=["expression", "other"],
                    ),
                ),
            },
            {"la": "a"},
        ),
        (
            # combine exclude_base works.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"a": "a"},
                        append={"'": "\N{COMBINING ACUTE ACCENT}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            "exclude_base",
                            ["append", ["map", "append"]],
                        ]
                    ),
                ),
            },
            {"la'": "\N{LATIN SMALL LETTER A WITH ACUTE}"},
        ),
        (
            # combine append works and includes the base map by default.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"a": "a"},
                        append={"'": "\N{COMBINING ACUTE ACCENT}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ]
                    ),
                ),
            },
            {
                "la": "a",
                "la'": "\N{LATIN SMALL LETTER A WITH ACUTE}",
            },
        ),
        (
            # Combining characters can stack, in any valid order.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"s": "s"},
                        append={
                            "*": "\N{COMBINING DOT ABOVE}",
                            ".": "\N{COMBINING DOT BELOW}",
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ]
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
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"a": "a"},
                        append={",": "\N{COMBINING CEDILLA}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ]
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
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"j": "j"},
                        append={
                            "~": "\N{COMBINING TILDE}",
                            ".": "\N{COMBINING DOT ABOVE}",
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ]
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
            # Characters without names are ignored by name_regex_replace.
            {
                "common": data.Group(
                    name="",
                    prefix="Z",
                    maps=dict(main={"NULL": "\x00"}),
                    name_regex_replace_maps=dict(
                        main={
                            "a": (
                                (re.compile(r".*"), r"LATIN SMALL LETTER A"),
                            ),
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["name_regex_replace", "main"],
                        ],
                    ),
                ),
            },
            {"ZNULL": "\x00"},
        ),
        (
            # combine name_regex_replace works and can stack with append.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"o": "o"},
                        append={"'": "\N{COMBINING ACUTE ACCENT}"},
                    ),
                    name_regex_replace_maps=dict(
                        main={
                            "/": ((re.compile(r".*"), r"\g<0> WITH STROKE"),),
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                            ["name_regex_replace", "main"],
                        ],
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
            # A combine name_regex_replace entry can have multiple replacement
            # rules.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={
                            "O": "O",
                            "o": "o",
                        },
                    ),
                    name_regex_replace_maps=dict(
                        main={
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
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["name_regex_replace", "main"],
                        ],
                    ),
                ),
            },
            {
                "lO": "O",
                "lo": "o",
                "lO/": "\N{LATIN CAPITAL LETTER O WITH STROKE}",
                "lo/": "\N{LATIN SMALL LETTER O WITH STROKE}",
            },
        ),
        (
            # combine name_regex_replace ignores incorrect names, but can match
            # corrected names.
            {
                "math": data.Group(
                    name="",
                    prefix="m",
                    maps=dict(
                        main={
                            "B": "B",
                            "P": "P",
                            "W": "W",
                        },
                    ),
                    name_regex_replace_maps=dict(
                        main={
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
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["name_regex_replace", "main"],
                        ],
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
                    name="",
                    prefix="l",
                    maps=dict(main={"o": "o"}),
                    name_regex_replace_maps=dict(
                        main={
                            "/": (
                                (
                                    re.compile(r"no match"),
                                    r"\g<0> WITH STROKE",
                                ),
                            ),
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["name_regex_replace", "main"],
                        ],
                    ),
                ),
            },
            {"lo": "o"},
        ),
        (
            # A regex that produces a name that does not exist is not an error.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(main={"o": "o"}),
                    name_regex_replace_maps=dict(
                        main={
                            "/": (
                                (
                                    re.compile(r".*"),
                                    r"\g<0> WITH A FAKE ACCENT",
                                ),
                            ),
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["name_regex_replace", "main"],
                        ],
                    ),
                ),
            },
            {"lo": "o"},
        ),
        (
            # "product" works and can produce unkown sequences.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        consonants={
                            "b": "b",
                            "c": "c",
                        },
                        vowels={
                            "a": "a",
                            "e": "e",
                        },
                        final_consonants={
                            "d": "d",
                        },
                    ),
                    expressions=dict(
                        main=[
                            "product",
                            ["map", "consonants"],
                            ["map", "vowels"],
                            ["map", "final_consonants"],
                        ],
                    ),
                ),
            },
            {
                "lbad": "bad",
                "lbed": "bed",
                "lcad": "cad",
                "lced": "ced",
            },
        ),
        (
            # "union" works.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        one={"a": "a"},
                        two={"b": "b"},
                    ),
                    expressions=dict(
                        main=["union", ["map", "one"], ["map", "two"]],
                    ),
                ),
            },
            {
                "la": "a",
                "lb": "b",
            },
        ),
        (
            # Mnemonics can overlap.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={
                            "a": "a",
                            "ae": "\N{LATIN SMALL LETTER AE}",
                        },
                        append={
                            "'": "\N{COMBINING ACUTE ACCENT}",
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
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
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"s": "s"},
                        append={
                            ".": "\N{COMBINING DOT ABOVE}",
                            "..": "\N{COMBINING DOT BELOW}",
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
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
                    name="",
                    prefix="g",
                    maps=dict(
                        main={"a": "\N{GREEK SMALL LETTER ALPHA}"},
                        append={"~": "\N{COMBINING GREEK PERISPOMENI}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
                    ),
                ),
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"a": "a"},
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
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
                    name="",
                    prefix="l",
                    maps=dict(main={"a": "a"}),
                    expressions=dict(main=["map", "main"]),
                ),
                "latin2": data.Group(
                    name="",
                    prefix="la",
                    maps=dict(
                        main={"": ""},
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
                    ),
                ),
            },
            {
                "la": "a",
                "la~": "\N{COMBINING TILDE}",
            },
        ),
        (
            # A mnemonic can have an empty result to allow typing combining
            # characters.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"_": ""},
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
                    ),
                ),
            },
            {"l_~": "\N{COMBINING TILDE}"},
        ),
        (
            # A mnemonic can itself be empty to allow typing combining
            # characters without any additional prefix.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    maps=dict(
                        main={"": ""},
                        append={"~": "\N{COMBINING TILDE}"},
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
                    ),
                ),
            },
            {"l~": "\N{COMBINING TILDE}"},
        ),
        (
            # Combining characters can stack over an empty result.
            {
                "regions": data.Group(
                    name="",
                    prefix="r",
                    maps=dict(
                        main={"": ""},
                        append={
                            "N": "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
                            "U": "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
                        },
                    ),
                    expressions=dict(
                        main=[
                            "combine",
                            ["map", "main"],
                            ["append", ["map", "append"]],
                        ],
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
        (
            # Examples work.
            {
                "latin": data.Group(
                    name="",
                    prefix="l",
                    examples={"a": "a"},
                    maps=dict(main={"a": "a"}),
                    expressions=dict(main=["map", "main"]),
                ),
            },
            {"la": "a"},
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
