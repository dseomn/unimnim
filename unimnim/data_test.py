# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib
import re
from typing import Any

import pytest

from unimnim import data


@pytest.mark.parametrize(
    "s,expected",
    (
        ("", ()),
        ("kumquat", ()),
        (
            "foo\N{LATIN SMALL LETTER N PRECEDED BY APOSTROPHE}bar",
            ("\N{LATIN SMALL LETTER N PRECEDED BY APOSTROPHE}",),
        ),
    ),
)
def test_discouraged_sequences(s: str, expected: tuple[str, ...]) -> None:
    assert frozenset(data.discouraged_sequences(s)) == frozenset(expected)


@pytest.mark.parametrize(
    "explicit_string,error_regex",
    (
        (":", r"Can't parse"),
        ("U+0068 LATIN SMALL LETTER H [foo]", "Invalid flag: 'foo'"),
        ("foo", r"not of the form"),
        ("U+0070 LATIN SMALL LETTER I", r"U\+0070 has name .* not"),
        ("U+0070 (NULL)", r"does not have alias"),  # alias for other char
        ("U+0070 (NOT AN ALIAS I HOPE)", r"does not have alias"),
        (
            (
                "U+0301 COMBINING ACUTE ACCENT [combining]: "
                "\N{LATIN SMALL LETTER A WITH GRAVE}"
            ),
            r"not the combining sequence at the end of",
        ),
        ("U+01A2 LATIN CAPITAL LETTER OI", r"has corrected name"),
        ("U+0069 LATIN SMALL LETTER I: foo", r"decodes to 'i' not 'foo'"),
        (
            "U+0061 LATIN SMALL LETTER A, U+0301 COMBINING ACUTE ACCENT",
            r"not NFC normalized",
        ),
        ("U+0068 LATIN SMALL LETTER H [precomposed]", r"is not precomposed"),
        ("U+00E0 LATIN SMALL LETTER A WITH GRAVE", r"is precomposed"),
        ("U+0149 LATIN SMALL LETTER N PRECEDED BY APOSTROPHE", r"discouraged"),
    ),
)
def test_parse_explicit_string_error(
    explicit_string: str, error_regex: str
) -> None:
    with pytest.raises(ValueError, match=error_regex):
        data.parse_explicit_string(explicit_string)


@pytest.mark.parametrize(
    "explicit_string,expected",
    (
        ("", ""),
        ("U+0000 (NULL)", "\x00"),
        ("U+0068 LATIN SMALL LETTER H", "h"),
        ("U+0068 LATIN SMALL LETTER H: h", "h"),
        ("U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I", "hi"),
        ("U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I: hi", "hi"),
        ("U+01A2 LATIN CAPITAL LETTER OI (LATIN CAPITAL LETTER GHA)", "\u01a2"),
        (
            "U+01A2 LATIN CAPITAL LETTER OI (LATIN CAPITAL LETTER GHA): \u01a2",
            "\u01a2",
        ),
        (
            (
                "U+0301 COMBINING ACUTE ACCENT [combining]: "
                "\N{LATIN SMALL LETTER A WITH ACUTE}"
            ),
            "\u0301",
        ),
        (
            "U+00E0 LATIN SMALL LETTER A WITH GRAVE [precomposed]",
            "\N{LATIN SMALL LETTER A WITH GRAVE}",
        ),
    ),
)
def test_parse_explicit_string(explicit_string: str, expected: str) -> None:
    assert data.parse_explicit_string(explicit_string) == expected


@pytest.mark.parametrize(
    "string,expected",
    (
        ("", ""),
        ("\x00", "U+0000"),  # This could be improved with a control alias.
        ("h", "U+0068 LATIN SMALL LETTER H: h"),
        ("hi", "U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I: hi"),
        (
            "\u01a2",
            "U+01A2 LATIN CAPITAL LETTER OI (LATIN CAPITAL LETTER GHA): \u01a2",
        ),
        (" ", "U+0020 SPACE"),
    ),
)
def test_to_explicit_string(string: str, expected: str) -> None:
    actual = data.to_explicit_string(string)
    assert actual == expected
    assert data.parse_explicit_string(actual) == string


@pytest.mark.parametrize(
    "raw,error_regex",
    (
        (dict(not_valid="foo"), r"Unexpected keys"),
        (
            dict(
                append={
                    "~": "U+0303 COMBINING TILDE",
                    "'": "U+0301 COMBINING ACUTE ACCENT",
                },
            ),
            r"combining\.append is not sorted",
        ),
        (
            dict(
                name_regex_replace={
                    "b": [["foo", "bar"]],
                    "a": [["foo", "bar"]],
                },
            ),
            r"combining\.name_regex_replace is not sorted",
        ),
    ),
)
def test_combining_parse_error(raw: Any, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        data.Combining.parse(raw)


@pytest.mark.parametrize(
    "raw,expected",
    (
        ({}, {}),
        (
            dict(append={"'": "U+0301 COMBINING ACUTE ACCENT"}),
            dict(append={"'": "\u0301"}),
        ),
        (
            dict(name_regex_replace={"/": [[r".*", r"\g<0> WITH STROKE"]]}),
            dict(
                name_regex_replace={
                    "/": ((re.compile(r".*"), r"\g<0> WITH STROKE"),)
                },
            ),
        ),
    ),
)
def test_combining_parse(raw: Any, expected: Any) -> None:
    assert data.Combining.parse(raw) == data.Combining(**expected)


@pytest.mark.parametrize(
    "raw,error_regex",
    (
        (
            dict(prefix="l", expressions={}, not_valid="foo"),
            r"Unexpected keys",
        ),
        (
            dict(
                prefix="l",
                maps=dict(
                    main={
                        "b": "U+0062 LATIN SMALL LETTER B",
                        "a": "U+0061 LATIN SMALL LETTER A",
                    },
                ),
                expressions={},
            ),
            r"maps\.main is not sorted",
        ),
        (
            dict(
                prefix="l",
                maps=dict(
                    main={
                        "b": "U+0061 LATIN SMALL LETTER A",
                        "a": "U+0061 LATIN SMALL LETTER A",
                    },
                ),
                expressions={},
            ),
            r"maps\.main is not sorted",
        ),
    ),
)
def test_group_parse_error(raw: Any, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        data.Group.parse(raw)


@pytest.mark.parametrize(
    "raw,expected",
    (
        (
            dict(prefix="l", expressions=dict(main=[[]])),
            dict(prefix="l", expressions=dict(main=[[]])),
        ),
        (
            dict(
                prefix="l",
                examples={"a": "U+0061 LATIN SMALL LETTER A"},
                name_maps=dict(main={"a": "A"}),
                maps=dict(main={"a": "U+0061 LATIN SMALL LETTER A"}),
                combining=dict(
                    main=dict(append={"'": "U+0301 COMBINING ACUTE ACCENT"}),
                ),
                expressions=dict(
                    main=[[["map", "main"], ["combining", "main"]]],
                ),
            ),
            dict(
                prefix="l",
                examples={"a": "a"},
                name_maps=dict(main={"a": "A"}),
                maps=dict(main={"a": "a"}),
                combining=dict(
                    main=data.Combining.parse(
                        dict(append={"'": "U+0301 COMBINING ACUTE ACCENT"})
                    ),
                ),
                expressions=dict(
                    main=[[["map", "main"], ["combining", "main"]]],
                ),
            ),
        ),
    ),
)
def test_group_parse(raw: Any, expected: Any) -> None:
    assert data.Group.parse(raw) == data.Group(**expected)


def test_load(tmp_path: pathlib.Path) -> None:
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "latin.toml").write_text(
        """
        prefix = "l"
        [maps.main]
        "a" = "U+0061 LATIN SMALL LETTER A"
        [expressions]
        main = [[["map", "main"]]]
        """
    )
    (tmp_path / "greek.toml").write_text(
        """
        prefix = "g"
        [maps.main]
        "a" = "U+03B1 GREEK SMALL LETTER ALPHA"
        [expressions]
        main = [[["map", "main"]]]
        """
    )

    actual = data.load(tmp_path)

    assert actual == {
        "subdir/latin": data.Group.parse(
            dict(
                prefix="l",
                maps=dict(main={"a": "U+0061 LATIN SMALL LETTER A"}),
                expressions=dict(main=[[["map", "main"]]]),
            )
        ),
        "greek": data.Group.parse(
            dict(
                prefix="g",
                maps=dict(main={"a": "U+03B1 GREEK SMALL LETTER ALPHA"}),
                expressions=dict(main=[[["map", "main"]]]),
            )
        ),
    }
