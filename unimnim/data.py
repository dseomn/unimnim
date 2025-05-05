# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Data file parsing."""

from collections.abc import Mapping
import dataclasses
import pathlib
import pprint
import re
import tomllib
from typing import Any, Self
import unicodedata


def parse_explicit_string(explicit_string: str, /) -> str:
    """Returns the value of an explicit string."""
    if not explicit_string:
        return ""
    string_match = re.fullmatch(
        (
            r"(?P<encoded_string>[^\[\]:]*)"
            r"(?: \[(?P<flags>[^\]]*)\])?"
            r"(?:: (?P<expected_string>.*))?"
        ),
        explicit_string,
    )
    if string_match is None:
        raise ValueError(f"Can't parse explicit string: {explicit_string!r}")
    encoded_string = string_match.group("encoded_string")
    match flags := string_match.group("flags"):
        case None:
            flag_combining = False
        case "combining":
            flag_combining = True
        case _:
            raise ValueError(f"Invalid flags: {flags!r}")
    expected_string = string_match.group("expected_string")
    code_points = []
    for code_point_string in encoded_string.split(", "):
        code_point_match = re.fullmatch(
            (
                r"U\+(?P<number>[0-9A-F]+)"
                r"(?: (?P<name>[^()]+))?"
                r"(?: \((?P<alias>.+)\))?"
            ),
            code_point_string,
        )
        if code_point_match is None:
            raise ValueError(
                "Code point is not of the form U+ABCD NAME (ALIAS): "
                f"{code_point_string!r}"
            )
        code_point = chr(int(code_point_match.group("number"), base=16))
        if (expected_name := code_point_match.group("name")) is not None:
            actual_name = unicodedata.name(code_point)
            if actual_name != expected_name:
                raise ValueError(
                    f"U+{code_point_match.group('number')} has name "
                    f"{actual_name!r} not {expected_name!r}"
                )
        if (alias := code_point_match.group("alias")) is not None:
            try:
                alias_value = unicodedata.lookup(alias)
            except KeyError:
                alias_value = None
            if alias_value != code_point:
                raise ValueError(
                    f"U+{code_point_match.group('number')} does not have alias "
                    f"{alias!r}"
                )
        code_points.append(code_point)
    decoded_string = "".join(code_points)
    if expected_string is not None:
        if flag_combining and not unicodedata.normalize(
            "NFD", expected_string
        ).endswith(decoded_string):
            raise ValueError(
                f"{explicit_string!r} decodes to {decoded_string!r} which is "
                f"not the combining sequence at the end of {expected_string!r}"
            )
        elif not flag_combining and expected_string != decoded_string:
            raise ValueError(
                f"{explicit_string!r} decodes to {decoded_string!r} not "
                f"{expected_string!r}"
            )
    return decoded_string


def _require_sorted_by_value_and_key(
    mapping: Mapping[str, str], /, *, name: str
) -> None:
    items = list(mapping.items())
    sorted_items = sorted(items, key=lambda kv: (kv[1], kv[0]))
    if items != sorted_items:
        raise ValueError(
            f"{name} is not sorted by value then key.\n"
            "Expected:\n"
            f"{pprint.pformat(dict(sorted_items), sort_dicts=False)}\n"
            "Actual:\n"
            f"{pprint.pformat(dict(items), sort_dicts=False)}"
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class Group:
    """Data for a single group of mnemonics.

    Attributes:
        prefix: Prefix for all of the group's mnemonics.
        base: Map from mnemonic (not including prefix) to a result.
        combining: Map from mnemonic (not including prefix) to a combining code
            point that should be added to an existing result.
    """

    prefix: str
    base: Mapping[str, str]
    combining: Mapping[str, str]

    def __post_init__(self) -> None:
        _require_sorted_by_value_and_key(self.base, name="base")
        _require_sorted_by_value_and_key(self.combining, name="combining")

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


def load(path: pathlib.Path, /) -> Mapping[str, Group]:
    """Loads groups from .toml files in a directory.

    Returns:
        Map from a group identifier to the group data.
    """
    return {
        str(file.relative_to(path)): Group.parse(
            tomllib.loads(file.read_text())
        )
        for file in path.glob("**/*.toml")
    }
