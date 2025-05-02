# Copyright 2025 David Mandelberg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Generates the input method from data."""

import collections
from collections.abc import Mapping
import pprint
import unicodedata

from unimnim import data


def _generate_map_one_script(
    script_id: str,
    script: data.Script,
) -> Mapping[str, str]:
    """Returns a map from mnemonic to result for one script."""
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
                f"Script {script_id!r} has duplicate mnemonic {mnemonic!r}"
            )

    for mnemonic, result in script.base.items():
        _add(script.prefix + mnemonic, result)
    for mnemonic, result in script.combining.items():
        _add(script.prefix + mnemonic, result)

    while combining_to_check:
        mnemonic, result = combining_to_check.popleft()
        for combining_mnemonic, combining_result in script.combining.items():
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


def generate_map(scripts: Mapping[str, data.Script]) -> Mapping[str, str]:
    """Returns a map from mnemonic to result."""
    result_and_script_id_by_mnemonic = collections.defaultdict[
        str, list[tuple[str, str]]
    ](list)
    for script_id, script in scripts.items():
        for mnemonic, result in _generate_map_one_script(
            script_id, script
        ).items():
            result_and_script_id_by_mnemonic[mnemonic].append(
                (result, script_id)
            )
    if duplicates := {
        k: v for k, v in result_and_script_id_by_mnemonic.items() if len(v) > 1
    }:
        raise ValueError(
            "Some scripts have the same mnemonics:\n"
            f"{pprint.pformat(duplicates)}"
        )
    return {
        mnemonic: result
        for mnemonic, ((result, _),) in result_and_script_id_by_mnemonic.items()
    }
