# Copyright 2025 David Mandelberg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pathlib
from typing import Any

import pytest

from unimnim import data


@pytest.mark.parametrize(
    "explicit_string,error_regex",
    (
        ("foo", r"not of the form"),
        ("U+0070 LATIN SMALL LETTER I", r"U\+0070 has name .* not"),
        ("U+0070 (NULL)", r"does not have alias"),  # alias for other char
        ("U+0070 (NOT AN ALIAS I HOPE)", r"does not have alias"),
        ("U+0069 LATIN SMALL LETTER I: foo", r"decodes to 'i' not 'foo'"),
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
    ),
)
def test_parse_explicit_string(explicit_string: str, expected: str) -> None:
    assert data.parse_explicit_string(explicit_string) == expected


def test_group_parse_error() -> None:
    with pytest.raises(ValueError, match="Unexpected keys"):
        data.Group.parse(dict(prefix="l", base={}, not_valid="foo"))


@pytest.mark.parametrize(
    "raw,expected",
    (
        (
            dict(prefix="l", base={"a": "U+0061 LATIN SMALL LETTER A"}),
            dict(prefix="l", base={"a": "a"}, combining={}),
        ),
        (
            dict(
                prefix="l",
                base={"a": "U+0061 LATIN SMALL LETTER A"},
                combining={"'": "U+0301 COMBINING ACUTE ACCENT"},
            ),
            dict(prefix="l", base={"a": "a"}, combining={"'": "\u0301"}),
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
