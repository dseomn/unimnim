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

from collections.abc import Mapping
import dataclasses
import pathlib
import re
import tomllib
from typing import Any, Self
import unicodedata


def parse_explicit_string(explicit_string: str, /) -> str:
    """Returns the value of an explicit string."""
    encoded_string, separator, expected_string = explicit_string.partition(": ")
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
            f"{explicit_string!r} decodes to {decoded_string!r} not "
            f"{expected_string!r}"
        )
    return decoded_string


@dataclasses.dataclass(frozen=True, kw_only=True)
class Script:
    """Data for a single script.

    Attributes:
        prefix: Prefix for all of the script's mnemonics.
        base: Map from mnemonic (not including prefix) to a result.
        combining: Map from mnemonic (not including prefix) to a combining code
            point that should be added to an existing result.
    """

    prefix: str
    base: Mapping[str, str]
    combining: Mapping[str, str]

    @classmethod
    def parse(cls, raw: Any, /) -> Self:
        """Returns the data parsed from the format used in data files."""
        if unexpected_keys := raw.keys() - {"prefix", "base", "combining"}:
            raise ValueError(f"Unexpected keys: {list(unexpected_keys)}")
        return cls(
            prefix=raw["prefix"],
            base={
                key: parse_explicit_string(value)
                for key, value in raw["base"].items()
            },
            combining={
                key: parse_explicit_string(value)
                for key, value in raw.get("combining", {}).items()
            },
        )


def load(path: pathlib.Path, /) -> Mapping[str, Script]:
    """Loads scripts from .toml files in a directory.

    Returns:
        Map from a script identifier to the script data.
    """
    return {
        str(file.relative_to(path)): Script.parse(
            tomllib.loads(file.read_text())
        )
        for file in path.glob("**/*.toml")
    }
