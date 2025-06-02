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
    commit: str = "",
    candidates: Sequence[str] = (),
    preedit: str = "",
) -> Any:
    return pytest.param(
        map_,
        keys,
        commit,
        candidates,
        preedit,
        id=id,
    )


@pytest.mark.parametrize(
    ",".join(
        (
            "map_",
            "keys",
            "commit",
            "candidates",
            "preedit",
        )
    ),
    (
        _param(
            "no_command",
            map_={"a": "b"},
            keys=("a",),
            commit="a",
        ),
        _param(
            "map_start",
            map_={"a": "b"},
            keys=_START,
            preedit=_PROMPT,
        ),
        _param(
            "map_invalid_key",
            map_={"a": "b"},
            keys=(*_START, "c"),
            commit="c",
        ),
        _param(
            "map_done",
            map_={"a": "b"},
            keys=(*_START, "a"),
            commit="b",
        ),
        _param(
            "map_done_then_mnemonic_without_command",
            map_={"a": "b"},
            keys=(*_START, "a", "a"),
            commit="ba",
        ),
        _param(
            "map_prefix",
            map_={"aa": "bb"},
            keys=(*_START, "a"),
            preedit=f"{_PROMPT}a",
        ),
        _param(
            "map_prefix_then_invalid_key",
            map_={"aa": "bb"},
            keys=(*_START, "a", "c"),
            commit="ac",
        ),
        _param(
            "map_prefix_then_unrelated_prefix",
            map_={"aa": "bb", "cc": "dd"},
            keys=(*_START, "a", "c"),
            commit="ac",
        ),
        _param(
            "map_prefix_then_new_command",
            map_={"aa": "bb"},
            keys=(*_START, "a", *_START, "a", "a"),
            commit="abb",
        ),
        _param(
            "map_prefix_then_done",
            map_={"aa": "bb"},
            keys=(*_START, "a", "a"),
            commit="bb",
        ),
        _param(
            "map_done_and_prefix",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a"),
            preedit="b",
        ),
        _param(
            "map_done_and_prefix_then_invalid_key",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a", "d"),
            commit="bd",
        ),
        _param(
            "map_done_and_prefix_then_longer_prefix_then_invalid_key",
            map_={"a": "b", "aaa": "c"},
            keys=(*_START, "a", "a", "d"),
            commit="aad",
        ),
        _param(
            "map_done_and_prefix_then_unrelated_prefix",
            map_={"a": "b", "aa": "c", "dd": "e"},
            keys=(*_START, "a", "f"),
            commit="bf",
        ),
        _param(
            "map_done_and_prefix_then_new_command",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a", *_START, "a", "a"),
            commit="bc",
        ),
        _param(
            "map_done_and_prefix_then_done",
            map_={"a": "b", "aa": "c"},
            keys=(*_START, "a", "a"),
            commit="c",
        ),
        _param(
            "search_prefix_start",
            map_={"aa": "b", "bb": "a"},
            keys=_SEARCH_PREFIX_START,
            candidates=(),
            preedit=_SEARCH_PREFIX_PROMPT,
        ),
        _param(
            "search_prefix_invalid_key",
            map_={"a": "b"},
            keys=(*_SEARCH_PREFIX_START, "c"),
            commit="c",
        ),
        _param(
            "search_prefix_done",
            map_={"a": "b"},
            keys=(*_SEARCH_PREFIX_START, "a"),
            candidates=("b",),
            preedit="b",
        ),
        _param(
            "search_prefix_done_then_invalid_key",
            map_={"a": "b"},
            keys=(*_SEARCH_PREFIX_START, "a", "c"),
            commit="bc",
        ),
        _param(
            "search_prefix_done_then_new_command",
            map_={"a": "b", "c": "d"},
            keys=(*_SEARCH_PREFIX_START, "a", *_SEARCH_PREFIX_START, "c"),
            commit="b",
            candidates=("d",),
            preedit="d",
        ),
        _param(
            "search_prefix_prefix",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a"),
            candidates=("bb",),
            preedit="bb",
        ),
        _param(
            "search_prefix_prefix_then_invalid_key",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a", "c"),
            commit="bbc",
        ),
        _param(
            "search_prefix_prefix_then_unrelated_prefix",
            map_={"aa": "bb", "cc": "dd"},
            keys=(*_SEARCH_PREFIX_START, "a", "c"),
            commit="bbc",
        ),
        _param(
            "search_prefix_prefix_then_new_command",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a", *_SEARCH_PREFIX_START, "a"),
            commit="bb",
            candidates=("bb",),
            preedit="bb",
        ),
        _param(
            "search_prefix_prefix_then_done",
            map_={"aa": "bb"},
            keys=(*_SEARCH_PREFIX_START, "a", "a"),
            candidates=("bb",),
            preedit="bb",
        ),
        _param(
            "search_prefix_done_and_prefix",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a"),
            candidates=("b", "c"),
            preedit="b",
        ),
        _param(
            "search_prefix_done_and_prefix_then_invalid_key",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a", "d"),
            commit="bd",
        ),
        _param(
            "search_prefix_done_and_prefix_then_unrelated_prefix",
            map_={"a": "b", "aa": "c", "dd": "e"},
            keys=(*_SEARCH_PREFIX_START, "a", "f"),
            commit="bf",
        ),
        _param(
            "search_prefix_done_and_prefix_then_new_command",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a", *_SEARCH_PREFIX_START, "a", "a"),
            commit="b",
            candidates=("c",),
            preedit="c",
        ),
        _param(
            "search_prefix_done_and_prefix_then_done",
            map_={"a": "b", "aa": "c"},
            keys=(*_SEARCH_PREFIX_START, "a", "a"),
            candidates=("c",),
            preedit="c",
        ),
        _param(
            "search_prefix_truncated_candidate_list",
            map_={f"a{i:04d}": f"b{i:04d}" for i in range(1001)},
            keys=(*_SEARCH_PREFIX_START, "a"),
            candidates=tuple(f"b{i:04d}" for i in range(1000)),
            preedit="b0000",
        ),
    ),
)
def test_m17n_input_method(
    map_: Mapping[str, str],
    keys: Sequence[str],
    commit: str,
    candidates: Sequence[str],
    preedit: str,
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
            "-t",
            commit,
            *(("-C",) if candidates else ()),
            *itertools.chain.from_iterable(
                ("-c", candidate) for candidate in candidates
            ),
            "-p",
            preedit,
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,  # See assert below.
        text=True,
        env={**os.environ, "M17NDIR": str(tmp_path)},
    )

    assert result.returncode == 0
