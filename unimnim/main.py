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
        "--write-all",
        type=pathlib.Path,
        help="Directory to write all output files to.",
    )
    parser.add_argument(
        "--write-m17n",
        type=pathlib.Path,
        help="File to write unimnim.mim to.",
    )
    parsed_args = parser.parse_args(args)

    if parsed_args.write_all is not None:
        parsed_args.write_all.mkdir(exist_ok=True)

    with resources.as_file(resources.files().joinpath("data")) as data_path:
        data_ = data.load(data_path)

    if parsed_args.write_all is not None:
        _write_json(
            parsed_args.write_all / "known_sequences.json",
            input_method.known_sequences(),
        )

    map_ = input_method.generate_map(data_)
    if parsed_args.write_all is not None:
        _write_json(parsed_args.write_all / "map.json", map_)

    prefix_map = input_method.generate_prefix_map(map_)
    if parsed_args.write_all is not None:
        _write_json(parsed_args.write_all / "prefix_map.json", prefix_map)

    m17n_mim = input_method.render_template(
        resources.files().joinpath("templates/m17n.mim.jinja").read_text(),
        map=map_,
        prefix_map=prefix_map,
    )
    if parsed_args.write_all is not None:
        (parsed_args.write_all / "unimnim.mim").write_text(m17n_mim)
    if parsed_args.write_m17n is not None:
        parsed_args.write_m17n.write_text(m17n_mim)

    if parsed_args.write_all is not None:
        _write_json(
            parsed_args.write_all / "coverage.json",
            coverage.report(covered=frozenset(map_.values())),
        )


if __name__ == "__main__":
    main()
