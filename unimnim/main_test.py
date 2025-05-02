# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from unimnim import main


def test_main(tmp_path: pathlib.Path) -> None:
    main.main(args=(f"--output={tmp_path}",))

    assert [str(f.relative_to(tmp_path)) for f in tmp_path.glob("**/*")] == [
        "map.json",
    ]
