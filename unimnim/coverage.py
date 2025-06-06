# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Tools to generate coverage information.

These are primarily designed to help with ideas of what should be added, and are
probably not very good for statistics about how comprehensive the data is.
"""

import collections
from collections.abc import Mapping, Set
from typing import Any

import icu

from unimnim import input_method


def _report_section(
    section: Mapping[str, Set[str]], *, covered: Set[str]
) -> Any:
    report = dict[str, Any]()
    for key, characters in section.items():
        missing = characters - covered
        report[key] = dict(
            total=len(characters),
            covered_count=len(characters & covered),
            missing_count=len(missing),
            missing=sorted(missing),
        )
    return report


def report(*, covered: Set[str]) -> Any:
    """Returns a coverage report as a JSON-encodable object."""
    # TODO: dseomn - Combine this data with keyboard layout info in a useful
    # way. The fact that "0" isn't covered by mnemonics using an en_US keyboard
    # isn't particularly interesting, because that keyboard has a 0 key. On the
    # other hand, if more mnemonics are added for other keyboards, having æ
    # covered by an æ key but not by an en_US keyboard key sequence isn't
    # particularly useful to en_US users.
    #
    # https://github.com/unicode-org/cldr/tree/main/keyboards looks interesting,
    # but somewhat limited, and I don't see an ICU API for it anyway.
    # https://github.com/Vyshantha/multiscripteditor/tree/main/editorClient/src/assets/keyboard-layouts
    # might work.

    characters_by_language = collections.defaultdict(set)
    for character, languages in input_method.known_sequences().items():
        for language in languages:
            characters_by_language[language].add(character)

    all_characters_by_script = collections.defaultdict(set)
    exemplar_characters_by_script = collections.defaultdict(set)
    for character, languages in input_method.known_sequences().items():
        for script_int in icu.Script.getScriptExtensions(character[0]):
            script = icu.Char.getPropertyValueName(
                icu.UProperty.SCRIPT, script_int
            )
            all_characters_by_script[script].add(character)
            if languages:
                exemplar_characters_by_script[script].add(character)

    return {
        "language": _report_section(characters_by_language, covered=covered),
        "scriptAll": _report_section(all_characters_by_script, covered=covered),
        "scriptExemplar": _report_section(
            exemplar_characters_by_script, covered=covered
        ),
    }
