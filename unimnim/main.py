# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Main entrypoint."""

import argparse
from collections.abc import Sequence
from importlib import resources
import json
import pathlib
import sys
from typing import Any

from unimnim import coverage
from unimnim import data
from unimnim import input_method


def _write_json(path: pathlib.Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main(
    *,
    args: Sequence[str] = sys.argv[1:],
) -> None:
    """Main.

    Args:
        args: Command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=pathlib.Path.cwd(),
        type=pathlib.Path,
        help="Directory to write output files to.",
    )
    parsed_args = parser.parse_args(args)

    with resources.as_file(resources.files().joinpath("data")) as data_path:
        data_ = data.load(data_path)

    _write_json(
        parsed_args.output / "known_sequences.json",
        input_method.known_sequences(),
    )

    map_ = input_method.generate_map(data_)
    _write_json(parsed_args.output / "map.json", map_)

    prefix_map = input_method.generate_prefix_map(map_)
    _write_json(parsed_args.output / "prefix_map.json", prefix_map)

    (parsed_args.output / "unimnim.mim").write_text(
        input_method.render_template(
            resources.files().joinpath("templates/m17n.mim.jinja").read_text(),
            map=map_,
            prefix_map=prefix_map,
        )
    )

    _write_json(
        parsed_args.output / "coverage.json",
        coverage.report(covered=frozenset(map_.values())),
    )


if __name__ == "__main__":
    main()
