# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Tools to generate coverage information.

These are primarily designed to help with ideas of what should be added, and are
probably not very good for statistics about how comprehensive the data is.
"""

import collections
from collections.abc import Set
from typing import Any

from unimnim import input_method


def report(*, covered: Set[str]) -> Any:
    """Returns a coverage report as a JSON-encodable object."""
    characters_by_language = collections.defaultdict(set)
    for character, languages in input_method.known_sequences().items():
        for language in languages:
            characters_by_language[language].add(character)

    # TODO: dseomn - Combine this data with keyboard layout info in a useful
    # way. The fact that "0" isn't covered by mnemonics using an en_US keyboard
    # isn't particularly interesting, because that keyboard has a 0 key. On the
    # other hand, if more mnemonics are added for other keyboards, having æ
    # covered by an æ key but not by an en_US keyboard key sequence isn't
    # particularly useful to en_US users.
    #
    # https://github.com/unicode-org/cldr/tree/main/keyboards looks interesting,
    # but somewhat limited, and I don't see an ICU API for it anyway.

    report = {}
    for language, characters in characters_by_language.items():
        missing = characters - covered
        report[language] = dict(
            total=len(characters),
            covered_count=len(characters & covered),
            missing_count=len(missing),
            missing=sorted(missing),
        )
    return report
