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
    expected_candidates_shown: bool | None = None,
    expected_candidates: Sequence[str] = (),
    expected_preedit: str = "",
    expected_committed: str = "",
) -> Any:
    return pytest.param(
        map_,
        keys,
        (
            bool(expected_candidates)
            if expected_candidates_shown is None
            else expected_candidates_shown
        ),
        expected_candidates,
        expected_preedit,
        expected_committed,
        id=id,
    )


@pytest.mark.parametrize(
    ",".join(
        (
            "map_",
            "keys",
            "expected_candidates_shown",
            "expected_candidates",
            "expected_preedit",
            "expected_committed",
        )
    ),
    (
        _param(
            "no_command",
            map_={"a": "b"},
            keys=("a",),
            expected_committed="a",
        ),
        _param(
            "map_start",
            map_={"a": "b"},
            keys=_START,
            expected_preedit=_PROMPT,
        ),
        _param(
            "map_invalid_key",
            map_={"a": "b"},
            keys=(*_START, "c"),
            expected_committed="c",
        ),
        _param(
            "map_done",
            map_={"a": "b"},
            keys=(*_START, "a"),
            expected_committed="b",
        ),
        _param(
            "map_done_then_mnemonic_without_command",
            map_={"a": "b"},
            keys=(*_START, "a", "a"),
            expected_committed="ba",
        ),
        _param(
            "map_prefix",
            map_={"aa": "bb"},
            keys=(*_START, "a"),
            expected_preedit=f"{_PROMPT}a",
        ),
        _param(
            "map_prefix_then_invalid_key",
            map_={"aa": "bb"},
            keys=(*_START, "a", "c"),
            expected_committed="ac",
        ),
        _param(
            "map_prefix_then_unrelated_prefix",
            map_={"aa": "bb", "cc": "dd"},
            keys=(*_START, "a", "c"),
            expected_committed="ac",
        ),
        _param(
            "map_prefix_then_done",
            map_={"aa": "bb"},
            keys=(*_START, "a", "a"),
            expected_committed="bb",
        ),
        _param(
            "map_done_and_prefix",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a"),
            expected_preedit="b",
        ),
        _param(
            "map_done_and_prefix_then_invalid_key",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a", "d"),
            expected_committed="bd",
        ),
        _param(
            "map_done_and_prefix_then_unrelated_prefix",
            map_={"a": "b", "aa": "c", "dd": "e"},
            keys=(*_START, "a", "f"),
            expected_committed="bf",
        ),
        _param(
            "map_done_and_prefix_then_done",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a", "a"),
            expected_committed="c",
        ),
        _param(
            "search_prefix_start",
            map_={"aa": "b", "bb": "a"},
            keys=_SEARCH_PREFIX_START,
            expected_candidates=(),
            expected_preedit=_SEARCH_PREFIX_PROMPT,
        ),
        _param(
            "search_prefix_invalid_key",
            map_={"a": "b"},
            keys=(*_SEARCH_PREFIX_START, "c"),
            expected_candidates_shown=True,  # Not useful, but not a problem.
            expected_committed="c",
        ),
        _param(
            "search_prefix_done",
            map_={"a": "b"},
            keys=(*_SEARCH_PREFIX_START, "a"),
            expected_candidates=("b",),
            expected_preedit="b",
        ),
        _param(
            "search_prefix_done_then_invalid_key",
            map_={"a": "b"},
            keys=(*_SEARCH_PREFIX_START, "a", "c"),
            expected_committed="bc",
        ),
        _param(
            "search_prefix_prefix",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a"),
            expected_candidates=("bb",),
            expected_preedit=f"bb",
        ),
        _param(
            "search_prefix_prefix_then_invalid_key",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a", "c"),
            expected_committed="bbc",
        ),
        _param(
            "search_prefix_prefix_then_unrelated_prefix",
            map_={"aa": "bb", "cc": "dd"},
            keys=(*_SEARCH_PREFIX_START, "a", "c"),
            expected_committed="bbc",
        ),
        _param(
            "search_prefix_prefix_then_done",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a", "a"),
            expected_candidates=("bb",),
            expected_preedit=f"bb",
        ),
        _param(
            "search_prefix_done_and_prefix",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a"),
            expected_candidates=("b", "c"),
            expected_preedit=f"b",
        ),
        _param(
            "search_prefix_done_and_prefix_then_invalid_key",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a", "d"),
            expected_committed=f"bd",
        ),
        _param(
            "search_prefix_done_and_prefix_then_unrelated_prefix",
            map_={"a": "b", "aa": "c", "dd": "e"},
            keys=(*_SEARCH_PREFIX_START, "a", "f"),
            expected_committed=f"bf",
        ),
        _param(
            "search_prefix_done_and_prefix_then_done",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a", "a"),
            expected_candidates=("c",),
            expected_preedit=f"c",
        ),
    ),
)
def test_m17n_input_method(
    map_: Mapping[str, str],
    keys: Sequence[str],
    expected_candidates_shown: bool,
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
            *(("-C",) if expected_candidates_shown else ()),
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
