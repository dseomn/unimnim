# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Data file parsing."""

from collections.abc import Callable, Collection, Mapping
import dataclasses
import pathlib
import pprint
import re
import tomllib
from typing import Any, Self
import unicodedata

import icu

# TODO: https://gitlab.pyicu.org/main/pyicu/-/issues/176 - Use a constant.
_DEPRECATED_CODE_POINTS = frozenset(
    icu.Char.getBinaryPropertySet(icu.Char.getPropertyEnum("Deprecated"))
)


def discouraged_sequences(s: str, /) -> Collection[str]:
    """Returns any discouraged sequences in the given string."""
    # TODO: dseomn - Find some way to access
    # https://www.unicode.org/Public/UNIDATA/DoNotEmit.txt from python and use
    # it here.
    return frozenset(s) & _DEPRECATED_CODE_POINTS


@dataclasses.dataclass(frozen=True, kw_only=True)
class _ExplicitStringFlags:
    # This uses a dataclass instead of enum.Flag because it might make sense to
    # add "flags" that are more like key-value pairs, and enum.Flag doesn't seem
    # to help with parsing at all anyway.

    combining: bool = False
    precomposed: bool = False

    @classmethod
    def parse(cls, flags_str: str | None, /) -> Self:
        if flags_str is None:
            return cls()
        kwargs = {}
        for flag_str in flags_str.split(","):
            match flag_str:
                case "combining":
                    kwargs["combining"] = True
                case "precomposed":
                    kwargs["precomposed"] = True
                case _:
                    raise ValueError(f"Invalid flag: {flag_str!r}")
        return cls(**kwargs)


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
    elif correction := icu.Char.charName(
        code_point, icu.UCharNameChoice.CHAR_NAME_ALIAS
    ):
        raise ValueError(
            f"U+{match.group('number')} has corrected name {correction}, but "
            "no alias was specified."
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
    flags = _ExplicitStringFlags.parse(match.group("flags"))
    expected_string = match.group("expected_string")
    decoded_string = "".join(
        map(_parse_explicit_code_point, encoded_string.split(", "))
    )
    if expected_string is not None:
        if flags.combining and not unicodedata.normalize(
            "NFD", expected_string
        ).endswith(decoded_string):
            raise ValueError(
                f"{explicit_string!r} decodes to {decoded_string!r} which is "
                f"not the combining sequence at the end of {expected_string!r}"
            )
        elif not flags.combining and expected_string != decoded_string:
            raise ValueError(
                f"{explicit_string!r} decodes to {decoded_string!r} not "
                f"{expected_string!r}"
            )
    if not unicodedata.is_normalized("NFC", decoded_string):
        raise ValueError(f"{explicit_string!r} is not NFC normalized.")
    if unicodedata.is_normalized("NFD", decoded_string) and flags.precomposed:
        raise ValueError(f"{explicit_string!r} is not precomposed.")
    elif (
        not unicodedata.is_normalized("NFD", decoded_string)
        and not flags.precomposed
    ):
        raise ValueError(f"{explicit_string!r} is precomposed.")
    if discouraged := discouraged_sequences(decoded_string):
        raise ValueError(
            f"{explicit_string!r} contains discouraged sequences "
            f"{list(discouraged)}"
        )
    return decoded_string


def to_explicit_string(string: str, /) -> str:
    """Returns an explicit string for the given regular string."""
    code_points_explicit = []
    for code_point in string:
        code_point_parts = [f"U+{ord(code_point):04X}"]
        if name := unicodedata.name(code_point, ""):
            code_point_parts.append(name)
        if correction := icu.Char.charName(
            code_point, icu.UCharNameChoice.CHAR_NAME_ALIAS
        ):
            code_point_parts.append(f"({correction})")
        code_points_explicit.append(" ".join(code_point_parts))
    encoded = ", ".join(code_points_explicit)
    if string and string.isprintable() and " " not in string:
        return f"{encoded}: {string}"
    else:
        return encoded


def _require_sorted(
    mapping: Mapping[str, Any],
    /,
    *,
    key: Callable[[Any], Any],
    key_description: str,
    name: str,
) -> None:
    items = list(mapping.items())
    sorted_items = sorted(items, key=key)
    if items != sorted_items:
        raise ValueError(
            f"{name} is not sorted by {key_description}.\n"
            "Expected:\n"
            f"{pprint.pformat(dict(sorted_items), sort_dicts=False)}\n"
            "Actual:\n"
            f"{pprint.pformat(dict(items), sort_dicts=False)}"
        )


def _require_sorted_by_key(mapping: Mapping[str, Any], /, *, name: str) -> None:
    _require_sorted(
        mapping,
        key=lambda kv: kv[0],
        key_description="key",
        name=name,
    )


def _require_sorted_by_value_and_key(
    mapping: Mapping[str, str], /, *, name: str
) -> None:
    _require_sorted(
        mapping,
        key=lambda kv: (kv[1], kv[0]),
        key_description="value then key",
        name=name,
    )


@dataclasses.dataclass(frozen=True, kw_only=True)
class Combining:
    """Data for combining mnemonics.

    Attributes:
        append: See unimnim/data/README.md
        name_regex_replace: See unimnim/data/README.md
    """

    append: Mapping[str, str] = dataclasses.field(default_factory=dict)
    name_regex_replace: Mapping[
        str, Collection[tuple[re.Pattern[str], str]]
    ] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_sorted_by_value_and_key(self.append, name="combining.append")
        _require_sorted_by_key(
            self.name_regex_replace, name="combining.name_regex_replace"
        )

    @classmethod
    def parse(cls, raw: Any, /) -> Self:
        """Returns the data parsed from the format used in data files."""
        if unexpected_keys := raw.keys() - {"append", "name_regex_replace"}:
            raise ValueError(f"Unexpected keys: {list(unexpected_keys)}")
        name_regex_replace = {}
        for key, rules in raw.get("name_regex_replace", {}).items():
            name_regex_replace[key] = tuple(
                (re.compile(regex_str), replacement)
                for regex_str, replacement in rules
            )
        return cls(
            append={
                key: parse_explicit_string(value)
                for key, value in raw.get("append", {}).items()
            },
            name_regex_replace=name_regex_replace,
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class Group:
    """Data for a single group of mnemonics.

    Attributes:
        prefix: Prefix for all of the group's mnemonics.
        examples: Map from mnemonic (not including prefix) to result, to give as
            examples of how the group works.
        name_maps: Maps from part of a mnemonic to part of a character name.
        maps: Maps from mnemonic (not including prefix) to a result.
        combining: Sets of rules for combining partial mnemonics with a map.
        expressions: How the above are combined.
    """

    prefix: str
    examples: Mapping[str, str] = dataclasses.field(default_factory=dict)
    name_maps: Mapping[str, Mapping[str, str]] = dataclasses.field(
        default_factory=dict
    )
    maps: Mapping[str, Mapping[str, str]] = dataclasses.field(
        default_factory=dict
    )
    combining: Mapping[str, Combining] = dataclasses.field(default_factory=dict)
    expressions: Mapping[str, Any]

    def __post_init__(self) -> None:
        for map_name, map_ in self.maps.items():
            _require_sorted_by_value_and_key(map_, name=f"maps.{map_name}")

    @classmethod
    def parse(cls, raw: Any, /) -> Self:
        """Returns the data parsed from the format used in data files."""
        if unexpected_keys := raw.keys() - {
            "prefix",
            "examples",
            "name_maps",
            "maps",
            "combining",
            "expressions",
        }:
            raise ValueError(f"Unexpected keys: {list(unexpected_keys)}")
        maps = {}
        for map_name, map_ in raw.get("maps", {}).items():
            maps[map_name] = {
                key: parse_explicit_string(value) for key, value in map_.items()
            }
        return cls(
            prefix=raw["prefix"],
            examples={
                key: parse_explicit_string(value)
                for key, value in raw.get("examples", {}).items()
            },
            name_maps=raw.get("name_maps", {}),
            maps=maps,
            combining={
                name: Combining.parse(combining_data)
                for name, combining_data in raw.get("combining", {}).items()
            },
            expressions=raw["expressions"],
        )


def load(path: pathlib.Path, /) -> Mapping[str, Group]:
    """Loads groups from a directory.

    Returns:
        Map from a group identifier to the group data.
    """
    return {
        str(file.relative_to(path)).removesuffix(".toml"): Group.parse(
            tomllib.loads(file.read_text())
        )
        for file in path.glob("**/*.toml")
    }
