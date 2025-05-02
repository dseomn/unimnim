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
