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
    """Returns a map from input keys to replacement string for one script."""
    mapping = {}
    combining_to_check = collections.deque[tuple[str, str]]()

    def _add(keys: str, value: str) -> None:
        # Allow duplicates only if the value is the same. That way if "." is dot
        # above and ".." is dot below, "..." can be generated in either order
        # without counting as a duplicate.
        if keys not in mapping:
            mapping[keys] = value
            combining_to_check.append((keys, value))
        elif mapping[keys] != value:
            raise ValueError(
                f"Script {script_id!r} has duplicate key sequence {keys!r}"
            )

    for base_keys, base_value in script.base.items():
        _add(script.prefix + base_keys, base_value)
    for combining_keys, combining_value in script.combining.items():
        _add(script.prefix + combining_keys, combining_value)

    while combining_to_check:
        keys, value = combining_to_check.popleft()
        for combining_keys, combining_value in script.combining.items():
            combined_value = unicodedata.normalize(
                "NFC", value + combining_value
            )
            if len(combined_value) != 1:
                # TODO: dseomn - Handle some characters that are multiple code
                # points.
                # https://www.unicode.org/Public/draft/ucd/NamedSequences.txt
                # looks like it should be the right place to find them, but see
                # https://github.com/mike-fabian/ibus-typing-booster/issues/698#issuecomment-2840304410
                # for limitations of that file.
                continue
            combined_keys = keys + combining_keys
            _add(combined_keys, combined_value)

    return mapping


def generate_map(scripts: Mapping[str, data.Script]) -> Mapping[str, str]:
    """Returns a map from input keys to replacement string."""
    value_and_script_id_by_keys = collections.defaultdict[
        str, list[tuple[str, str]]
    ](list)
    for script_id, script in scripts.items():
        for keys, value in _generate_map_one_script(script_id, script).items():
            value_and_script_id_by_keys[keys].append((value, script_id))
    if duplicates := {
        k: v for k, v in value_and_script_id_by_keys.items() if len(v) > 1
    }:
        raise ValueError(
            "Some scripts have the same input key sequences:\n"
            f"{pprint.pformat(duplicates)}"
        )
    return {
        keys: value
        for keys, ((value, _),) in value_and_script_id_by_keys.items()
    }
