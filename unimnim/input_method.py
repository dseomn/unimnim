# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Generates the input method from data."""

import collections
from collections.abc import Iterable, Mapping, Sequence, Set
import dataclasses
import functools
import itertools
import pprint
from typing import Any
import unicodedata

import icu
import jinja2

from unimnim import data

_TEXT_VARIATION_SELECTOR = "\N{VARIATION SELECTOR-15}"
_EMOJI_VARIATION_SELECTOR = "\N{VARIATION SELECTOR-16}"


@functools.cache
def known_sequences() -> Mapping[str, Sequence[str]]:
    """Returns a map from known sequences to languages they're from.

    The languages can be empty for known sequences with unknown language.
    """
    # TODO: dseomn - Add sequences from
    # https://www.unicode.org/Public/UNIDATA/NamedSequences.txt and
    # https://www.unicode.org/Public/UNIDATA/NamedSequencesProv.txt
    sequences = collections.defaultdict[str, set[str]](set)

    def _add(sequence: str, *, language: str | None = None) -> None:
        if data.discouraged_sequences(sequence):
            return
        languages = sequences[unicodedata.normalize("NFC", sequence)]
        if language is not None:
            languages.add(language)

    for code_point_num in range(0x10FFFF + 1):
        code_point = chr(code_point_num)
        if unicodedata.category(code_point) not in (
            "Cn",  # unassigned
            "Co",  # private use
            "Cs",  # surrogate
        ):
            _add(code_point)

    for language in icu.Locale.getISOLanguages():
        locale = icu.Locale(language)
        locale_data = icu.LocaleData(language)
        for exemplar_type in (
            icu.ULocaleDataExemplarSetType.ES_STANDARD,
            icu.ULocaleDataExemplarSetType.ES_AUXILIARY,
            # TODO: https://gitlab.pyicu.org/main/pyicu/-/issues/175 - Use a
            # named constant for ES_PUNCTUATION.
            3,
        ):
            for sequence in locale_data.getExemplarSet(
                icu.USET_ADD_CASE_MAPPINGS, exemplar_type
            ):
                _add(sequence, language=language)
        numbering_system = icu.NumberingSystem.createInstance(locale)
        if not numbering_system.isAlgorithmic():
            for digit in numbering_system.getDescription():
                _add(digit, language=language)

    for uproperty in (icu.UProperty.EMOJI, icu.UProperty.RGI_EMOJI):
        for emoji in icu.Char.getBinaryPropertySet(uproperty):
            _add(emoji, language="emoji")
            if len(emoji) == 2 and emoji[1] == _EMOJI_VARIATION_SELECTOR:
                # TODO: dseomn - Use emoji-variation-sequences.txt for this
                # instead of guessing based on RGI_EMOJI.
                _add(
                    f"{emoji[0]}{_TEXT_VARIATION_SELECTOR}",
                    language="text-presentation",
                )

    return {
        sequence: sorted(languages) for sequence, languages in sequences.items()
    }


@functools.cache
def _known_sequences_and_prefixes() -> Set[str]:
    """Returns known sequences and prefixes of it."""
    result = set()
    for sequence in known_sequences():
        for prefix_len in range(1, len(sequence) + 1):
            result.add(sequence[:prefix_len])
    return result


def _lookup_correct_name(name: str) -> str:
    """Like unicodedata.lookup, but excludes incorrect names."""
    result = unicodedata.lookup(name)
    name_corrected = icu.Char.charName(
        result, icu.UCharNameChoice.CHAR_NAME_ALIAS
    )
    if name_corrected and name_corrected != name:
        raise KeyError(name)
    return result


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Map:
    """An intermediate map from mnemonic to result.

    Attributes:
        group_id: Group ID that the map is from.
        all_: Complete map, including unknown results.
        known: Map with only known results.
    """

    group_id: str
    all_: dict[str, str] = dataclasses.field(default_factory=dict)
    known: dict[str, str] = dataclasses.field(default_factory=dict)

    def add(self, mnemonic: str, result: str, *, is_known: bool = True) -> bool:
        """Adds an entry to the map, and returns whether it's new or not."""
        if discouraged := data.discouraged_sequences(result):
            raise ValueError(
                f"Mnemonic {mnemonic!r} has result {result!r} with discouraged "
                f"sequences {list(discouraged)}"
            )
        # Allow duplicates only if the result is the same. That way if "." is
        # dot above and ".." is dot below, "..." can be generated in either
        # order without counting as a duplicate.
        if mnemonic not in self.all_:
            self.all_[mnemonic] = result
            if is_known and result:
                self.known[mnemonic] = result
            return True
        elif self.all_[mnemonic] != result:
            raise ValueError(
                f"Group {self.group_id!r} has duplicate mnemonic {mnemonic!r}"
            )
        else:
            if is_known and result:
                self.known[mnemonic] = result
            return False

    def add_all(self, other: "_Map", /) -> None:
        """Adds all entries from the other map."""
        for mnemonic, result in other.all_.items():
            self.add(mnemonic, result, is_known=mnemonic in other.known)


def _names_maps_to_map(
    name_maps: Iterable[Mapping[str, str]], *, group_id: str
) -> _Map:
    """Returns a map from the cartesian product of name maps."""
    map_ = _Map(group_id=group_id)
    for items in itertools.product(
        *(name_map.items() for name_map in name_maps)
    ):
        mnemonic_parts = []
        name_parts = []
        for mnemonic_part, name_part in items:
            mnemonic_parts.append(mnemonic_part)
            name_parts.append(name_part)
        try:
            result_raw = _lookup_correct_name("".join(name_parts))
        except KeyError:
            continue
        map_.add(
            "".join(mnemonic_parts), unicodedata.normalize("NFC", result_raw)
        )
    return map_


def _cartesian_product(a: _Map, b: _Map, /) -> _Map:
    """Returns the cartesian product of two maps."""
    result = _Map(group_id=a.group_id)
    for a_mnemonic, a_result in a.all_.items():
        a_known = a_mnemonic in a.known or not a_result
        for b_mnemonic, b_result in b.all_.items():
            b_known = b_mnemonic in b.known or not b_result
            combined_result = unicodedata.normalize("NFC", a_result + b_result)
            result.add(
                a_mnemonic + b_mnemonic,
                combined_result,
                is_known=(
                    (a_known and b_known)
                    or combined_result in known_sequences()
                ),
            )
    return result


def _apply_combining(map_: _Map, combining: data.Combining) -> None:
    """Applies combining config to a map."""
    combining_to_check = collections.deque[tuple[str, str]](map_.all_.items())

    def _add(mnemonic: str, result: str, *, is_known: bool = True) -> None:
        if map_.add(mnemonic, result, is_known=is_known):
            combining_to_check.append((mnemonic, result))

    while combining_to_check:
        mnemonic, result = combining_to_check.popleft()

        for (
            combining_mnemonic,
            combining_result,
        ) in combining.append.items():
            combined_result = unicodedata.normalize(
                "NFC", result + combining_result
            )
            if combined_result not in _known_sequences_and_prefixes():
                continue
            combined_mnemonic = mnemonic + combining_mnemonic
            _add(
                combined_mnemonic,
                combined_result,
                is_known=combined_result in known_sequences(),
            )

        if len(result) != 1:
            continue
        # TODO: dseomn - Check the control names from NameAliases.txt, so that
        # name_regex_replace can be used for
        # https://en.wikipedia.org/wiki/Control_Pictures
        result_name = icu.Char.charName(
            result, icu.UCharNameChoice.CHAR_NAME_ALIAS
        ) or unicodedata.name(result, "")
        if not result_name:
            continue

        for (
            combining_mnemonic,
            rules,
        ) in combining.name_regex_replace.items():
            for combining_pattern, combining_replacement in rules:
                match = combining_pattern.fullmatch(result_name)
                if match is None:
                    continue
                combined_name = match.expand(combining_replacement)
                try:
                    combined_raw = _lookup_correct_name(combined_name)
                except KeyError:
                    continue
                combined_result = unicodedata.normalize("NFC", combined_raw)
                combined_mnemonic = mnemonic + combining_mnemonic
                _add(combined_mnemonic, combined_result)


@dataclasses.dataclass(frozen=True)
class _ReferenceTrackingDict[T]:
    """Dict that keeps track of which items are references."""

    data: dict[str, T]
    _: dataclasses.KW_ONLY
    referenced_keys: set[str] = dataclasses.field(default_factory=set)
    error_context: str
    type_name: str

    def get(self, key: str) -> T:
        """Returns the value for the given key."""
        try:
            value = self.data[key]
        except KeyError:
            raise ValueError(
                f"{self.error_context} does not have {self.type_name} {key!r}"
            ) from None
        else:
            self.referenced_keys.add(key)
            return value

    def require_all_referenced(self) -> None:
        if unreferenced := self.data.keys() - self.referenced_keys:
            raise ValueError(
                f"{self.error_context} defines but does not use "
                f"{self.type_name} {list(unreferenced)}"
            )


def _generate_map_one_group(
    group_id: str,
    group: data.Group,
) -> Mapping[str, str]:
    """Returns a map from mnemonic to result for one group."""
    name_maps = _ReferenceTrackingDict[Mapping[str, str]](
        dict(group.name_maps),
        error_context=f"Group {group_id!r}",
        type_name="name_map",
    )

    maps = _ReferenceTrackingDict[_Map](
        {},
        error_context=f"Group {group_id!r}",
        type_name="map",
    )
    for map_name, map_data in group.maps.items():
        maps.data[map_name] = _Map(group_id=group_id)
        for mnemonic, result in map_data.items():
            maps.data[map_name].add(mnemonic, result)

    combining = _ReferenceTrackingDict[data.Combining](
        dict(group.combining),
        error_context=f"Group {group_id!r}",
        type_name="combining",
    )

    expressions = _ReferenceTrackingDict[_Map](
        {},
        error_context=f"Group {group_id!r}",
        type_name="expression",
    )
    for expression_name, expression in group.expressions.items():
        expression_map = _Map(group_id=group_id)
        for union_operand_expr in expression:
            union_operand_map = _Map(group_id=group_id)
            # Add an empty entry so that the cartesian product with another map
            # returns that other map.
            union_operand_map.add("", "")
            for operation in union_operand_expr:
                match operation:
                    case ["name_maps", *name_map_names] if all(
                        isinstance(name, str) for name in name_map_names
                    ):
                        union_operand_map = _cartesian_product(
                            union_operand_map,
                            _names_maps_to_map(
                                map(name_maps.get, name_map_names),
                                group_id=group_id,
                            ),
                        )
                    case ["map", str() as map_name]:
                        union_operand_map = _cartesian_product(
                            union_operand_map, maps.get(map_name)
                        )
                    case ["combining", str() as combining_name]:
                        _apply_combining(
                            union_operand_map, combining.get(combining_name)
                        )
                    case ["expression", str() as ref_name]:
                        union_operand_map = _cartesian_product(
                            union_operand_map, expressions.get(ref_name)
                        )
                    case _:
                        raise ValueError(
                            f"Group {group_id!r} has invalid expression: "
                            f"{operation!r}"
                        )
            expression_map.add_all(union_operand_map)
        expressions.data[expression_name] = expression_map

    main_map = expressions.get("main")

    name_maps.require_all_referenced()
    maps.require_all_referenced()
    combining.require_all_referenced()
    expressions.require_all_referenced()

    return {
        group.prefix + mnemonic: result
        for mnemonic, result in main_map.known.items()
    }


def generate_map(groups: Mapping[str, data.Group]) -> Mapping[str, str]:
    """Returns a map from mnemonic to result."""
    result_and_group_id_by_mnemonic = collections.defaultdict[
        str, list[tuple[str, str]]
    ](list)
    for group_id, group in groups.items():
        for mnemonic, result in _generate_map_one_group(
            group_id, group
        ).items():
            result_and_group_id_by_mnemonic[mnemonic].append((result, group_id))
    if duplicates := {
        k: v for k, v in result_and_group_id_by_mnemonic.items() if len(v) > 1
    }:
        raise ValueError(
            "Some groups have the same mnemonics:\n"
            f"{pprint.pformat(duplicates)}"
        )
    result_by_mnemonic = {
        mnemonic: result
        for mnemonic, ((result, _),) in result_and_group_id_by_mnemonic.items()
    }
    return {
        mnemonic: result
        for mnemonic, result in sorted(
            result_by_mnemonic.items(), key=lambda kv: (kv[1], kv[0])
        )
    }


def generate_prefix_map(map_: Mapping[str, str]) -> Mapping[str, Sequence[str]]:
    """Returns a map from mnemonic prefix to matching results."""
    prefix_map = collections.defaultdict[str, list[str]](list)
    for mnemonic, result in map_.items():
        for prefix_len in range(len(mnemonic) + 1):
            results = prefix_map[mnemonic[:prefix_len]]
            if result not in results:
                results.append(result)
    return prefix_map


def m17n_mtext(s: str) -> str:
    """Returns the given string as m17n MTEXT."""
    # The documentation at
    # https://www.nongnu.org/m17n/manual-en/m17nDBFormat.html does not fully and
    # correctly describe the format, so this implementation is based on how
    # read_mtext_element() works in
    # https://git.savannah.nongnu.org/cgit/m17n/m17n-lib.git/tree/src/plist.c
    result = ['"']
    for i, c in enumerate(s):
        if c in r"\"":
            result.append(f"\\{c}")
        elif c.isprintable() or (ord(c) >= 0x80 and i > 0):
            # TODO: https://savannah.nongnu.org/bugs/index.php?67107 - Remove
            # all of the condition except for c.isprintable().
            result.append(c)
        else:
            # Note the space at the end. read_hexadesimal() seems to read hex
            # indefinitely, and read_mtext_element() only calls UNGETC() on
            # next_c if it's not a space. I.e., the trailing space both ends
            # read_hexadesimal() and is discarded by read_mtext_element().
            result.append(f"\\u{ord(c):X} ")
    result.append('"')
    return "".join(result)


def render_template(template: str, **kwargs: Any) -> str:
    """Returns a rendered jinja template.

    Args:
        template: Template contents.
        **kwargs: Context for the template.
    """
    jinja_env = jinja2.Environment(
        extensions=["jinja2.ext.do"],
        undefined=jinja2.StrictUndefined,
        autoescape=False,
    )
    jinja_env.filters["m17n_mtext"] = m17n_mtext
    return jinja_env.from_string(template).render(**kwargs)
