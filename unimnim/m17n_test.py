# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
from importlib import resources
import itertools
import os
import pathlib
import subprocess

import pytest

from unimnim import input_method

_PROMPT = "·"
_SEARCH_PREFIX_PROMPT = "·"

_START = ("A-\\",)
_SEARCH_PREFIX_START = ("A-\\", "A-\\")


@pytest.mark.parametrize(
    "map_,keys,expected_candidates,expected_preedit,expected_committed",
    (
        (
            # No command, input method ignores key.
            {"a": "b"},
            ("a",),
            (),
            "",
            "a",
        ),
        (
            # Shows prompt when starting a mnemonic.
            {"a": "b"},
            _START,
            (),
            _PROMPT,
            "",
        ),
        (
            # Commits the result.
            {"a": "b"},
            (*_START, "a"),
            (),
            "",
            "b",
        ),
    ),
)
def test_m17n_input_method(
    map_: Mapping[str, str],
    keys: Sequence[str],
    expected_candidates: Sequence[str],
    expected_preedit: str,
    expected_committed: str,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "unimnim.mim").write_text(
        input_method.render_template(
            (
                resources.files("unimnim")
                .joinpath("templates/m17n.mim.jinja")
                .read_text()
            ),
            map=map_,
            prefix_map=input_method.generate_prefix_map(map_),
            version="no-version-test-only",
        )
    )
    assert __spec__.origin is not None
    m17n_test = str(
        pathlib.Path(__spec__.origin).parent.parent / "tools" / "m17n-test"
    )

    result = subprocess.run(
        (
            m17n_test,
            "-l",
            "t",
            "-n",
            "unimnim",
            *itertools.chain.from_iterable(("-i", key) for key in keys),
            *(("-C",) if expected_candidates else ()),
            *itertools.chain.from_iterable(
                ("-c", candidate) for candidate in expected_candidates
            ),
            "-p",
            expected_preedit,
            "-t",
            expected_committed,
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,  # See assert below.
        text=True,
        env={**os.environ, "M17NDIR": str(tmp_path)},
    )

    assert result.returncode == 0
