# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
from importlib import resources
import itertools
import os
import pathlib
import subprocess
import textwrap
from typing import Any

import pytest

from unimnim import input_method

_PROMPT = "[prompt]"
_SEARCH_PREFIX_PROMPT = "[search-prefix-prompt]"

_START = ("A-\\",)
_SEARCH_PREFIX_START = ("A-\\", "A-\\")


# TODO: https://github.com/pytest-dev/pytest/issues/9216 - Delete this.
def _param(
    id: str,
    *,
    map_: Mapping[str, str],
    keys: Sequence[str],
    expected_candidates: Sequence[str] = (),
    expected_preedit: str = "",
    expected_committed: str = "",
) -> Any:
    return pytest.param(
        map_,
        keys,
        expected_candidates,
        expected_preedit,
        expected_committed,
        id=id,
    )


@pytest.mark.parametrize(
    "map_,keys,expected_candidates,expected_preedit,expected_committed",
    (
        _param(
            "key_passed_through_with_no_command",
            map_={"a": "b"},
            keys=("a",),
            expected_committed="a",
        ),
        _param(
            "start",
            map_={"a": "b"},
            keys=_START,
            expected_preedit=_PROMPT,
        ),
        _param(
            "commits_when_no_other_possible_mnemonics",
            map_={"a": "b"},
            keys=(*_START, "a"),
            expected_committed="b",
        ),
        _param(
            "search_prefix_start",
            map_={"aa": "b", "bb": "a"},
            keys=_SEARCH_PREFIX_START,
            expected_candidates=(),
            expected_preedit=_SEARCH_PREFIX_PROMPT,
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
    (tmp_path / "config.mic").write_text(
        textwrap.dedent(
            f"""
            ((input-method t unimnim)
             (variable
              (prompt nil {input_method.m17n_mtext(_PROMPT)})
              (search-prefix-prompt
               nil
               {input_method.m17n_mtext(_SEARCH_PREFIX_PROMPT)})
              )
             )
            """
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
