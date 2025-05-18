# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Generates the input method from data."""

import collections
from collections.abc import Mapping, Sequence, Set
import functools
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
    sequences = collections.defaultdict(set)

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
                sequences[unicodedata.normalize("NFC", sequence)].add(language)
        numbering_system = icu.NumberingSystem.createInstance(locale)
        if not numbering_system.isAlgorithmic():
            for digit in numbering_system.getDescription():
                sequences[unicodedata.normalize("NFC", digit)].add(language)

    # Some single code points like U+FB31 HEBREW LETTER BET WITH DAGESH are
    # neither NFC normalized, nor are their NFC normalizations in (current as of
    # 2025-05-06) exemplar data.
    for code_point in range(0x10FFFF + 1):
        code_point_nfc = unicodedata.normalize("NFC", chr(code_point))
        if len(code_point_nfc) > 1:
            sequences[code_point_nfc]  # create it if it doesn't exist

    for uproperty in (icu.UProperty.EMOJI, icu.UProperty.RGI_EMOJI):
        for emoji in icu.Char.getBinaryPropertySet(uproperty):
            sequences[emoji].add("emoji")
            if len(emoji) == 2 and emoji[1] == _EMOJI_VARIATION_SELECTOR:
                # TODO: dseomn - Use emoji-variation-sequences.txt for this
                # instead of guessing based on RGI_EMOJI.
                sequences[f"{emoji[0]}{_TEXT_VARIATION_SELECTOR}"].add(
                    "text-presentation"
                )

    return {
        sequence: sorted(languages) for sequence, languages in sequences.items()
    }


@functools.cache
def _known_sequences_and_prefixes() -> Set[str]:
    """Returns known sequences and prefixes of it with length > 1."""
    result = set()
    for sequence in known_sequences():
        for prefix_len in range(2, len(sequence) + 1):
            result.add(sequence[:prefix_len])
    return result


def _generate_map_one_group(
    group_id: str,
    group: data.Group,
) -> Mapping[str, str]:
    """Returns a map from mnemonic to result for one group."""
    mapping_all = {}
    mapping_known = {}
    combining_to_check = collections.deque[tuple[str, str]]()

    def _add(mnemonic: str, result: str, *, is_known: bool = True) -> None:
        if discouraged := data.discouraged_sequences(result):
            raise ValueError(
                f"Mnemonic {mnemonic!r} has result {result!r} with discouraged "
                f"sequences {list(discouraged)}"
            )
        # Allow duplicates only if the result is the same. That way if "." is
        # dot above and ".." is dot below, "..." can be generated in either
        # order without counting as a duplicate.
        if mnemonic not in mapping_all:
            mapping_all[mnemonic] = result
            if is_known and result:
                mapping_known[mnemonic] = result
            combining_to_check.append((mnemonic, result))
        elif mapping_all[mnemonic] != result:
            raise ValueError(
                f"Group {group_id!r} has duplicate mnemonic {mnemonic!r}"
            )

    for mnemonic, result in group.base.items():
        _add(group.prefix + mnemonic, result)

    while combining_to_check:
        mnemonic, result = combining_to_check.popleft()

        for (
            combining_mnemonic,
            combining_result,
        ) in group.combining.append.items():
            combined_result = unicodedata.normalize(
                "NFC", result + combining_result
            )
            if (
                len(combined_result) != 1
                and combined_result not in _known_sequences_and_prefixes()
            ):
                continue
            combined_mnemonic = mnemonic + combining_mnemonic
            _add(
                combined_mnemonic,
                combined_result,
                is_known=(
                    len(combined_result) == 1
                    or combined_result in known_sequences()
                ),
            )

        if len(result) != 1:
            continue
        if (result_name := unicodedata.name(result, None)) is None:
            continue

        for (
            combining_mnemonic,
            rules,
        ) in group.combining.name_regex_replace.items():
            for combining_pattern, combining_replacement in rules:
                match = combining_pattern.fullmatch(result_name)
                if match is None:
                    continue
                combined_name = match.expand(combining_replacement)
                try:
                    combined_raw = unicodedata.lookup(combined_name)
                except KeyError:
                    continue
                combined_name_corrected = icu.Char.charName(
                    combined_raw, icu.UCharNameChoice.CHAR_NAME_ALIAS
                )
                if combined_name_corrected and (
                    combined_name_corrected != combined_name
                ):
                    continue
                combined_result = unicodedata.normalize("NFC", combined_raw)
                combined_mnemonic = mnemonic + combining_mnemonic
                _add(combined_mnemonic, combined_result)

    return mapping_known


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
    return {
        mnemonic: result
        for mnemonic, ((result, _),) in result_and_group_id_by_mnemonic.items()
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
