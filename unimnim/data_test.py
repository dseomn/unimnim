# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
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
    "explicit_string,kwargs,expected",
    (
        ("", {}, ""),
        ("U+0000 (NULL)", {}, "\x00"),
        ("U+0068 LATIN SMALL LETTER H", {}, "h"),
        ("U+0068 LATIN SMALL LETTER H: h", {}, "h"),
        ("U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I", {}, "hi"),
        (
            "U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I: hi",
            {},
            "hi",
        ),
        (
            "U+01A2 LATIN CAPITAL LETTER OI (LATIN CAPITAL LETTER GHA)",
            {},
            "\u01a2",
        ),
        (
            "U+01A2 LATIN CAPITAL LETTER OI (LATIN CAPITAL LETTER GHA): \u01a2",
            {},
            "\u01a2",
        ),
        (
            (
                "U+0301 COMBINING ACUTE ACCENT [combining]: "
                "\N{LATIN SMALL LETTER A WITH ACUTE}"
            ),
            {},
            "\u0301",
        ),
        (
            "U+00E0 LATIN SMALL LETTER A WITH GRAVE [precomposed]",
            {},
            "\N{LATIN SMALL LETTER A WITH GRAVE}",
        ),
        (
            "U+00E0 LATIN SMALL LETTER A WITH GRAVE",
            dict(check_precomposed=False),
            "\N{LATIN SMALL LETTER A WITH GRAVE}",
        ),
    ),
)
def test_parse_explicit_string(
    explicit_string: str,
    kwargs: Mapping[str, Any],
    expected: str,
) -> None:
    assert data.parse_explicit_string(explicit_string, **kwargs) == expected


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
        (
            dict(
                prefix="l",
                name_regex_replace_maps=dict(
                    main={
                        "b": [["foo", "bar"]],
                        "a": [["foo", "bar"]],
                    },
                ),
                expressions={},
            ),
            r"name_regex_replace_maps\.main is not sorted",
        ),
    ),
)
def test_group_parse_error(raw: Any, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        data.Group.parse(raw, group_id="")


@pytest.mark.parametrize(
    "group_id,raw,expected",
    (
        (
            "Latn",
            dict(prefix="l", expressions=dict(main=["union"])),
            dict(name="Latin", prefix="l", expressions=dict(main=["union"])),
        ),
        (
            "not-a-valid-script",
            dict(prefix="l", expressions=dict(main=["union"])),
            dict(
                name="not-a-valid-script",
                prefix="l",
                expressions=dict(main=["union"]),
            ),
        ),
        (
            "Latn",
            dict(
                name="This is a group!",
                prefix="l",
                examples={"a'": "U+00E1 LATIN SMALL LETTER A WITH ACUTE"},
                name_maps=dict(main={"a": "A"}),
                maps=dict(main={"a": "U+0061 LATIN SMALL LETTER A"}),
                name_regex_replace_maps=dict(
                    main={"/": [[r".*", r"\g<0> WITH STROKE"]]},
                ),
                expressions=dict(main=["union"]),
            ),
            dict(
                name="This is a group!",
                prefix="l",
                examples={"a'": "\N{LATIN SMALL LETTER A WITH ACUTE}"},
                name_maps=dict(main={"a": "A"}),
                maps=dict(main={"a": "a"}),
                name_regex_replace_maps=dict(
                    main={"/": ((re.compile(r".*"), r"\g<0> WITH STROKE"),)},
                ),
                expressions=dict(main=["union"]),
            ),
        ),
    ),
)
def test_group_parse(group_id: str, raw: Any, expected: Any) -> None:
    assert data.Group.parse(raw, group_id=group_id) == data.Group(**expected)


def test_load(tmp_path: pathlib.Path) -> None:
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "latin.toml").write_text(
        """
        prefix = "l"
        [maps.main]
        "a" = "U+0061 LATIN SMALL LETTER A"
        [expressions]
        main = ["map", "main"]
        """
    )
    (tmp_path / "greek.toml").write_text(
        """
        prefix = "g"
        [maps.main]
        "a" = "U+03B1 GREEK SMALL LETTER ALPHA"
        [expressions]
        main = ["map", "main"]
        """
    )

    actual = data.load(tmp_path)

    assert actual == {
        "subdir/latin": data.Group.parse(
            dict(
                prefix="l",
                maps=dict(main={"a": "U+0061 LATIN SMALL LETTER A"}),
                expressions=dict(main=["map", "main"]),
            ),
            group_id="subdir/latin",
        ),
        "greek": data.Group.parse(
            dict(
                prefix="g",
                maps=dict(main={"a": "U+03B1 GREEK SMALL LETTER ALPHA"}),
                expressions=dict(main=["map", "main"]),
            ),
            group_id="greek",
        ),
    }
