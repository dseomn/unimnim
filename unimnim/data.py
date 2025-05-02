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
"""Data file parsing."""

import re
import unicodedata


def parse_string(s: str, /) -> str:
    """Returns the value of a human-readable string of unicode code points.

    Args:
        s: A string of the form "U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL
            LETTER I" or "U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER
            I: hi"
    """
    encoded_string, separator, expected_string = s.partition(": ")
    code_points = []
    for code_point_string in encoded_string.split(", "):
        if (
            match := re.fullmatch(r"U\+([0-9A-F]+) (.+)", code_point_string)
        ) is None:
            raise ValueError(
                "Code point is not of the form U+ABCD NAME: "
                f"{code_point_string!r}"
            )
        code_point = chr(int(match.group(1), base=16))
        expected_name = match.group(2)
        actual_name = unicodedata.name(code_point)
        if actual_name != expected_name:
            raise ValueError(
                f"U+{match.group(1)} has name {actual_name!r} not "
                f"{expected_name!r}"
            )
        code_points.append(code_point)
    decoded_string = "".join(code_points)
    if separator and expected_string != decoded_string:
        raise ValueError(
            f"{s!r} decodes to {decoded_string!r} not {expected_string!r}"
        )
    return decoded_string
