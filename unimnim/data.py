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


def _parse_explicit_code_point(explicit: str) -> str:
    match = re.fullmatch(
        (
            r"U\+(?P<number>[0-9A-F]+)"
            r"(?: (?P<name>[^()]+))?"
            r"(?: \((?P<alias>.+)\))?"
        ),
        explicit,
    )
    if match is None:
        raise ValueError(
            f"Code point is not of the form U+ABCD NAME (ALIAS): {explicit!r}"
        )
    code_point = chr(int(match.group("number"), base=16))
    if (expected_name := match.group("name")) is not None:
        actual_name = unicodedata.name(code_point)
        if actual_name != expected_name:
            raise ValueError(
                f"U+{match.group('number')} has name {actual_name!r} not "
                f"{expected_name!r}"
            )
    if (alias := match.group("alias")) is not None:
        try:
            alias_value = unicodedata.lookup(alias)
        except KeyError:
            alias_value = None
        if alias_value != code_point:
            raise ValueError(
                f"U+{match.group('number')} does not have alias {alias!r}"
            )
    return code_point


def parse_explicit_string(explicit_string: str, /) -> str:
    """Returns the value of an explicit string."""
    if not explicit_string:
        return ""
    match = re.fullmatch(
        (
            r"(?P<encoded_string>[^\[\]:]*)"
            r"(?: \[(?P<flags>[^\]]*)\])?"
            r"(?:: (?P<expected_string>.*))?"
        ),
        explicit_string,
    )
    if match is None:
        raise ValueError(f"Can't parse explicit string: {explicit_string!r}")
    encoded_string = match.group("encoded_string")
    match flags := match.group("flags"):
        case None:
            flag_combining = False
        case "combining":
            flag_combining = True
        case _:
            raise ValueError(f"Invalid flags: {flags!r}")
    expected_string = match.group("expected_string")
    decoded_string = "".join(
        map(_parse_explicit_code_point, encoded_string.split(", "))
    )
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
    if not unicodedata.is_normalized("NFC", decoded_string):
        raise ValueError(f"{explicit_string!r} is not NFC normalized.")
    if not unicodedata.is_normalized("NFD", decoded_string):
        # This is meant to catch accidentally adding a precomposed result to
        # base when a separate base and combining mnemonic would be better. It
        # probably makes sense to add a flag to bypass this check if/when any
        # base mnemonics want to intentionally have a precomposed result.
        raise ValueError(f"{explicit_string!r} is precomposed.")
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
