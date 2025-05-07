# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib
from typing import Any

import pytest

from unimnim import data


@pytest.mark.parametrize(
    "explicit_string,error_regex",
    (
        (":", r"Can't parse"),
        ("U+0068 LATIN SMALL LETTER H [foo]", "Invalid flags: 'foo'"),
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
        ("U+0069 LATIN SMALL LETTER I: foo", r"decodes to 'i' not 'foo'"),
        (
            "U+0061 LATIN SMALL LETTER A, U+0301 COMBINING ACUTE ACCENT",
            r"not NFC normalized",
        ),
        ("U+00E0 LATIN SMALL LETTER A WITH GRAVE", r"is precomposed"),
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
    ),
)
def test_parse_explicit_string(explicit_string: str, expected: str) -> None:
    assert data.parse_explicit_string(explicit_string) == expected


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
    ),
)
def test_combining_parse(raw: Any, expected: Any) -> None:
    assert data.Combining.parse(raw) == data.Combining(**expected)


@pytest.mark.parametrize(
    "raw,error_regex",
    (
        (dict(prefix="l", base={}, not_valid="foo"), r"Unexpected keys"),
        (
            dict(
                prefix="l",
                base={
                    "b": "U+0062 LATIN SMALL LETTER B",
                    "a": "U+0061 LATIN SMALL LETTER A",
                },
            ),
            r"base is not sorted",
        ),
        (
            dict(
                prefix="l",
                base={
                    "b": "U+0061 LATIN SMALL LETTER A",
                    "a": "U+0061 LATIN SMALL LETTER A",
                },
            ),
            r"base is not sorted",
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
            dict(prefix="l", base={"a": "U+0061 LATIN SMALL LETTER A"}),
            dict(prefix="l", base={"a": "a"}),
        ),
        (
            dict(
                prefix="l",
                base={"a": "U+0061 LATIN SMALL LETTER A"},
                combining=dict(append={"'": "U+0301 COMBINING ACUTE ACCENT"}),
            ),
            dict(
                prefix="l",
                base={"a": "a"},
                combining=data.Combining.parse(
                    dict(append={"'": "U+0301 COMBINING ACUTE ACCENT"})
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
        [base]
        "a" = "U+0061 LATIN SMALL LETTER A"
        """
    )
    (tmp_path / "greek.toml").write_text(
        """
        prefix = "g"
        [base]
        "a" = "U+03B1 GREEK SMALL LETTER ALPHA"
        """
    )

    actual = data.load(tmp_path)

    assert actual == {
        "subdir/latin.toml": data.Group.parse(
            dict(prefix="l", base={"a": "U+0061 LATIN SMALL LETTER A"})
        ),
        "greek.toml": data.Group.parse(
            dict(prefix="g", base={"a": "U+03B1 GREEK SMALL LETTER ALPHA"})
        ),
    }
