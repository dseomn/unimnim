# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence, Set
import contextlib
import pathlib

import pytest

from unimnim import main


@pytest.mark.parametrize(
    "args,expected_files",
    (
        ((), set()),
        (
            ("--write-all=output",),
            {
                "output",
                "output/known_sequences.json",
                "output/known_sequences.toml",
                "output/map.json",
                "output/prefix_map.json",
                "output/unimnim.mim",
                "output/coverage.json",
            },
        ),
        (("--write-m17n=unimnim.mim",), {"unimnim.mim"}),
    ),
)
def test_main(
    args: Sequence[str],
    expected_files: Set[str],
    tmp_path: pathlib.Path,
) -> None:
    with contextlib.chdir(tmp_path):
        main.main(args=args)

    assert {
        str(f.relative_to(tmp_path)) for f in tmp_path.glob("**/*")
    } == expected_files
