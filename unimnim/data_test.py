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

import collections
import pathlib
from typing import Any

import pytest

from unimnim import data


@pytest.mark.parametrize(
    "s,error_regex",
    (
        ("foo", r"not of the form"),
        ("U+0070 LATIN SMALL LETTER I", r"U\+0070 has name .* not"),
        ("U+0069 LATIN SMALL LETTER I: foo", r"decodes to 'i' not 'foo'"),
    ),
)
def test_parse_string_error(s: str, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        data.parse_string(s)


@pytest.mark.parametrize(
    "s,expected",
    (
        ("U+0068 LATIN SMALL LETTER H", "h"),
        ("U+0068 LATIN SMALL LETTER H: h", "h"),
        ("U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I", "hi"),
        ("U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I: hi", "hi"),
    ),
)
def test_parse_string(s: str, expected: str) -> None:
    assert data.parse_string(s) == expected


def test_script_parse_error() -> None:
    with pytest.raises(ValueError, match="Unexpected keys"):
        data.Script.parse(dict(prefix="l", base={}, not_valid="foo"))


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
def test_script_parse(raw: Any, expected: Any) -> None:
    assert data.Script.parse(raw) == data.Script(**expected)


def test_load(tmp_path: pathlib.Path) -> None:
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "Latin.toml").write_text(
        """
        prefix = "l"
        [base]
        "a" = "U+0061 LATIN SMALL LETTER A"
        """
    )
    (tmp_path / "Greek.toml").write_text(
        """
        prefix = "g"
        [base]
        "a" = "U+03B1 GREEK SMALL LETTER ALPHA"
        """
    )

    actual = data.load(tmp_path)

    expected = (
        data.Script.parse(
            dict(prefix="l", base={"a": "U+0061 LATIN SMALL LETTER A"})
        ),
        data.Script.parse(
            dict(prefix="g", base={"a": "U+03B1 GREEK SMALL LETTER ALPHA"})
        ),
    )
    assert collections.Counter(actual) == collections.Counter(expected)
