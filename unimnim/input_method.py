# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Generates the input method from data."""

import collections
from collections.abc import Mapping
import pprint
from typing import Any
import unicodedata

import jinja2

from unimnim import data


def _generate_map_one_group(
    group_id: str,
    group: data.Group,
) -> Mapping[str, str]:
    """Returns a map from mnemonic to result for one group."""
    mapping = {}
    combining_to_check = collections.deque[tuple[str, str]]()

    def _add(mnemonic: str, result: str) -> None:
        # Allow duplicates only if the result is the same. That way if "." is
        # dot above and ".." is dot below, "..." can be generated in either
        # order without counting as a duplicate.
        if mnemonic not in mapping:
            mapping[mnemonic] = result
            combining_to_check.append((mnemonic, result))
        elif mapping[mnemonic] != result:
            raise ValueError(
                f"Group {group_id!r} has duplicate mnemonic {mnemonic!r}"
            )

    for mnemonic, result in group.base.items():
        _add(group.prefix + mnemonic, result)
    for mnemonic, result in group.combining.items():
        _add(group.prefix + mnemonic, result)

    while combining_to_check:
        mnemonic, result = combining_to_check.popleft()
        for combining_mnemonic, combining_result in group.combining.items():
            combined_result = unicodedata.normalize(
                "NFC", result + combining_result
            )
            if len(combined_result) != 1:
                # TODO: dseomn - Handle some results that are multiple code
                # points.
                # https://www.unicode.org/Public/draft/ucd/NamedSequences.txt
                # looks like it should be the right place to find them, but see
                # https://github.com/mike-fabian/ibus-typing-booster/issues/698#issuecomment-2840304410
                # for limitations of that file.
                continue
            combined_mnemonic = mnemonic + combining_mnemonic
            _add(combined_mnemonic, combined_result)

    return mapping


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
