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

from collections.abc import Mapping

import pytest

from unimnim import data
from unimnim import input_method


@pytest.mark.parametrize(
    "scripts,error_regex",
    (
        (
            {
                "Latin": data.Script(
                    prefix="l",
                    base={"a": "a", "a'": "b"},
                    combining={"'": "\N{COMBINING ACUTE ACCENT}"},
                ),
            },
            "Script 'Latin' has duplicate",
        ),
        (
            {
                "Latin1": data.Script(
                    prefix="l",
                    base={"a": "a"},
                    combining={},
                ),
                "Latin2": data.Script(
                    prefix="l",
                    base={"a": "a"},
                    combining={},
                ),
            },
            "scripts have the same mnemonics",
        ),
    ),
)
def test_generate_map_error(
    scripts: Mapping[str, data.Script],
    error_regex: str,
) -> None:
    with pytest.raises(ValueError, match=error_regex):
        input_method.generate_map(scripts)


@pytest.mark.parametrize(
    "scripts,expected",
    (
        (
            # Combining characters can stack, in any valid order.
            {
                "Latin": data.Script(
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
                "l*": "\N{COMBINING DOT ABOVE}",
                "l.": "\N{COMBINING DOT BELOW}",
            },
        ),
        (
            # Base mnemonics can overlap.
            {
                "Latin": data.Script(
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
                "l'": "\N{COMBINING ACUTE ACCENT}",
            },
        ),
        (
            # Combining mnemonics can overlap. Overlapping combining mnemonics
            # can even stack together, as long as the order isn't important.
            {
                "Latin": data.Script(
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
                "l.": "\N{COMBINING DOT ABOVE}",
                "l..": "\N{COMBINING DOT BELOW}",
            },
        ),
        (
            # Different scripts can give different meanings to the same
            # mnemonics.
            {
                "Greek": data.Script(
                    prefix="g",
                    base={"a": "\N{GREEK SMALL LETTER ALPHA}"},
                    combining={"~": "\N{COMBINING GREEK PERISPOMENI}"},
                ),
                "Latin": data.Script(
                    prefix="l",
                    base={"a": "a"},
                    combining={"~": "\N{COMBINING TILDE}"},
                ),
            },
            {
                "ga": "\N{GREEK SMALL LETTER ALPHA}",
                "ga~": "\N{GREEK SMALL LETTER ALPHA WITH PERISPOMENI}",
                "g~": "\N{COMBINING GREEK PERISPOMENI}",
                "la": "a",
                "la~": "\N{LATIN SMALL LETTER A WITH TILDE}",
                "l~": "\N{COMBINING TILDE}",
            },
        ),
    ),
)
def test_generate_map(
    scripts: Mapping[str, data.Script],
    expected: Mapping[str, str],
) -> None:
    assert input_method.generate_map(scripts) == expected
