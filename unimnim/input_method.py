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


@functools.cache
def known_sequences() -> Mapping[str, Sequence[str]]:
    """Returns a map from known sequences to languages they're from."""
    sequences = collections.defaultdict(set)
    for language in icu.Locale.getISOLanguages():
        locale_data = icu.LocaleData(language)
        for exemplar_type in (
            icu.ULocaleDataExemplarSetType.ES_STANDARD,
            icu.ULocaleDataExemplarSetType.ES_AUXILIARY,
            # TODO: dseomn - File a feature request at
            # https://gitlab.pyicu.org/main/pyicu to get ES_PUNCTUATION from
            # https://github.com/unicode-org/icu/blob/48597a4897e8cfea3aad5be7a4e8143c852876a5/icu4c/source/i18n/unicode/ulocdata.h#L54C5-L54C28
            # added.
            3,
        ):
            for sequence in locale_data.getExemplarSet(
                icu.USET_ADD_CASE_MAPPINGS, exemplar_type
            ):
                sequences[unicodedata.normalize("NFC", sequence)].add(language)
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
        # Allow duplicates only if the result is the same. That way if "." is
        # dot above and ".." is dot below, "..." can be generated in either
        # order without counting as a duplicate.
        if mnemonic not in mapping_all:
            mapping_all[mnemonic] = result
            if is_known:
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
        for combining_mnemonic, combining_result in group.combining.items():
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
        if result
    }


def generate_prefix_map(map_: Mapping[str, str]) -> Mapping[str, Sequence[str]]:
    """Returns a map from mnemonic prefix to matching results."""
    prefix_map = collections.defaultdict[str, list[str]](list)
    for mnemonic, result in map_.items():
        for prefix_len in range(len(mnemonic) + 1):
            prefix_map[mnemonic[:prefix_len]].append(result)
    return prefix_map


def m17n_mtext(s: str) -> str:
    """Returns the given string as m17n MTEXT."""
    # The documentation at
    # https://www.nongnu.org/m17n/manual-en/m17nDBFormat.html does not fully and
    # correctly describe the format, so this implementation is based on how
    # read_mtext_element() works in
    # https://git.savannah.nongnu.org/cgit/m17n/m17n-lib.git/tree/src/plist.c
    result = ['"']
    for c in s:
        if c in r"\"":
            result.append(f"\\{c}")
        elif c.isprintable():
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
