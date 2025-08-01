# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Generates the input method from data."""

import collections
from collections.abc import Collection, Iterable, Mapping, Sequence, Set
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


def _extended_grapheme_clusters(s: str, /) -> Iterable[str]:
    if len(s) == 1:
        # This optimization makes the tests take about ~88% as long as without
        # it.
        yield s
        return
    it = icu.BreakIterator.createCharacterInstance(icu.Locale.getRoot())
    icu_string = icu.UnicodeString(s)
    it.setText(icu_string)
    for start, end in itertools.pairwise(itertools.chain((0,), it)):
        yield str(icu_string[start:end])


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
        for extended_grapheme_cluster in _extended_grapheme_clusters(
            unicodedata.normalize("NFC", sequence)
        ):
            languages = sequences[extended_grapheme_cluster]
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

    def add(
        self,
        mnemonic: str,
        result_raw: str,
        *,
        is_known: bool = True,
    ) -> None:
        """Adds an entry to the map."""
        result = unicodedata.normalize("NFC", result_raw)
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
        elif self.all_[mnemonic] != result:
            raise ValueError(
                f"Group {self.group_id!r} has duplicate mnemonic {mnemonic!r}"
            )
        elif is_known and result:
            self.known[mnemonic] = result

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
        map_.add("".join(mnemonic_parts), result_raw)
    return map_


def _apply_combining(
    base: _Map,
    *,
    exclude_base: bool,
    append_maps: Collection[_Map],
    name_regex_replace_maps: Collection[data.NameRegexReplaceMap],
) -> _Map:
    """Applies combining."""
    combined_map = _Map(group_id=base.group_id)
    combining_to_check = collections.deque[tuple[str, str]](base.all_.items())
    added_to_queue = set(base.all_)
    if not exclude_base:
        combined_map.add_all(base)

    def _add(mnemonic: str, result: str, *, is_known: bool = True) -> None:
        combined_map.add(mnemonic, result, is_known=is_known)
        if mnemonic not in added_to_queue:
            combining_to_check.append((mnemonic, result))
            added_to_queue.add(mnemonic)

    def _combine_append(
        append_map: _Map,
        *,
        base_mnemonic: str,
        base_result: str,
    ) -> None:
        for combining_mnemonic, combining_result in append_map.all_.items():
            combined_result = unicodedata.normalize(
                "NFC", base_result + combining_result
            )
            if combined_result not in _known_sequences_and_prefixes():
                continue
            combined_mnemonic = base_mnemonic + combining_mnemonic
            _add(
                combined_mnemonic,
                combined_result,
                is_known=combined_result in known_sequences(),
            )

    def _combine_name_regex_replace(
        name_regex_replace_map: data.NameRegexReplaceMap,
        *,
        base_mnemonic: str,
        base_result: str,
    ) -> None:
        if len(base_result) != 1:
            return
        # TODO: dseomn - Check the control names from NameAliases.txt, so that
        # name_regex_replace can be used for
        # https://en.wikipedia.org/wiki/Control_Pictures
        base_result_name = icu.Char.charName(
            base_result, icu.UCharNameChoice.CHAR_NAME_ALIAS
        ) or unicodedata.name(base_result, "")
        if not base_result_name:
            return
        for combining_mnemonic, rules in name_regex_replace_map.items():
            for combining_pattern, combining_replacement in rules:
                match = combining_pattern.fullmatch(base_result_name)
                if match is None:
                    continue
                combined_name = match.expand(combining_replacement)
                try:
                    combined_raw = _lookup_correct_name(combined_name)
                except KeyError:
                    continue
                combined_mnemonic = base_mnemonic + combining_mnemonic
                _add(combined_mnemonic, combined_raw)

    while combining_to_check:
        mnemonic, result = combining_to_check.popleft()
        for append_map in append_maps:
            _combine_append(
                append_map,
                base_mnemonic=mnemonic,
                base_result=result,
            )
        for name_regex_replace_map in name_regex_replace_maps:
            _combine_name_regex_replace(
                name_regex_replace_map,
                base_mnemonic=mnemonic,
                base_result=result,
            )

    return combined_map


def _cartesian_product(*maps: _Map, group_id: str) -> _Map:
    """Returns the cartesian product of maps."""
    result = _Map(group_id=group_id)
    for items in itertools.product(*(map_.all_.items() for map_ in maps)):
        mnemonic_parts = []
        result_parts = []
        parts_known = []
        for map_index, (mnemonic_part, result_part) in enumerate(items):
            mnemonic_parts.append(mnemonic_part)
            result_parts.append(result_part)
            parts_known.append(
                mnemonic_part in maps[map_index].known or not result_part
            )
        combined_result = unicodedata.normalize("NFC", "".join(result_parts))
        result.add(
            "".join(mnemonic_parts),
            combined_result,
            is_known=all(parts_known) or combined_result in known_sequences(),
        )
    return result


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


@dataclasses.dataclass(frozen=True, kw_only=True)
class _GroupState:
    name_maps: _ReferenceTrackingDict[Mapping[str, str]]
    maps: _ReferenceTrackingDict[_Map]
    name_regex_replace_maps: _ReferenceTrackingDict[data.NameRegexReplaceMap]
    expressions: _ReferenceTrackingDict[_Map]


def _evaluate_expression(
    expression: Any,
    *,
    group_id: str,
    state: _GroupState,
) -> _Map:
    evaluate = functools.partial(
        _evaluate_expression,
        group_id=group_id,
        state=state,
    )
    match expression:
        case ["name_maps", *name_map_names] if all(
            isinstance(name, str) for name in name_map_names
        ):
            return _names_maps_to_map(
                map(state.name_maps.get, name_map_names),
                group_id=group_id,
            )
        case ["map", str() as map_name]:
            return state.maps.get(map_name)
        case ["expression", str() as ref_name]:
            return state.expressions.get(ref_name)
        case ["combine", base_expr, *options]:
            base = evaluate(base_expr)
            exclude_base = False
            append_maps = []
            name_regex_replace_maps = []
            for option in options:
                match option:
                    case "exclude_base":
                        exclude_base = True
                    case ["append", append_expr]:
                        append_maps.append(evaluate(append_expr))
                    case ["name_regex_replace", str(map_name)]:
                        name_regex_replace_maps.append(
                            state.name_regex_replace_maps.get(map_name)
                        )
                    case _:
                        raise ValueError(
                            f"Group {group_id!r} has invalid 'combine' option: "
                            f"{option!r}"
                        )
            return _apply_combining(
                base,
                exclude_base=exclude_base,
                append_maps=append_maps,
                name_regex_replace_maps=name_regex_replace_maps,
            )
        case ["product", *operands]:
            return _cartesian_product(
                *map(evaluate, operands),
                group_id=group_id,
            )
        case ["union", *operands]:
            map_ = _Map(group_id=group_id)
            for operand in operands:
                map_.add_all(evaluate(operand))
            return map_
        case _:
            raise ValueError(
                f"Group {group_id!r} has invalid expression: {expression!r}"
            )


def _generate_map_one_group(
    group_id: str,
    group: data.Group,
) -> Mapping[str, str]:
    """Returns a map from mnemonic to result for one group."""
    state = _GroupState(
        name_maps=_ReferenceTrackingDict(
            dict(group.name_maps),
            error_context=f"Group {group_id!r}",
            type_name="name_map",
        ),
        maps=_ReferenceTrackingDict(
            {},
            error_context=f"Group {group_id!r}",
            type_name="map",
        ),
        name_regex_replace_maps=_ReferenceTrackingDict(
            dict(group.name_regex_replace_maps),
            error_context=f"Group {group_id!r}",
            type_name="name_regex_replace_map",
        ),
        expressions=_ReferenceTrackingDict(
            {},
            error_context=f"Group {group_id!r}",
            type_name="expression",
        ),
    )

    for map_name, map_data in group.maps.items():
        state.maps.data[map_name] = _Map(group_id=group_id)
        for mnemonic, result in map_data.items():
            state.maps.data[map_name].add(mnemonic, result)

    for expression_name, expression in group.expressions.items():
        state.expressions.data[expression_name] = _evaluate_expression(
            expression,
            group_id=group_id,
            state=state,
        )

    main_map = state.expressions.get("main")

    state.name_maps.require_all_referenced()
    state.maps.require_all_referenced()
    state.name_regex_replace_maps.require_all_referenced()
    state.expressions.require_all_referenced()

    for example_mnemonic, example_result in group.examples.items():
        if example_mnemonic not in main_map.known:
            raise ValueError(
                f"Group {group_id!r} has example {example_mnemonic!r} that "
                "does not exist."
            )
        elif main_map.known[example_mnemonic] != example_result:
            raise ValueError(
                f"Group {group_id!r} has example {example_mnemonic!r} that "
                f"should map to {example_result!r} but actually maps to "
                f"{main_map.known[example_mnemonic]!r}."
            )

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
    prefix_map = collections.defaultdict[str, set[str]](set)
    for mnemonic, result in map_.items():
        for prefix_len in range(len(mnemonic) + 1):
            prefix_map[mnemonic[:prefix_len]].add(result)
    return {prefix: sorted(results) for prefix, results in prefix_map.items()}


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
