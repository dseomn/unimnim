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

from unimnim import coverage
from unimnim import data
from unimnim import input_method


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

    (parsed_args.output / "known_sequences.json").write_text(
        json.dumps(input_method.known_sequences(), ensure_ascii=False, indent=2)
    )

    map_ = input_method.generate_map(data_)
    (parsed_args.output / "map.json").write_text(
        json.dumps(map_, ensure_ascii=False, indent=2)
    )

    prefix_map = input_method.generate_prefix_map(map_)
    (parsed_args.output / "prefix_map.json").write_text(
        json.dumps(prefix_map, ensure_ascii=False, indent=2)
    )

    (parsed_args.output / "m17n.mim").write_text(
        input_method.render_template(
            resources.files().joinpath("templates/m17n.mim.jinja").read_text(),
            map=map_,
            prefix_map=prefix_map,
        )
    )

    (parsed_args.output / "coverage.json").write_text(
        json.dumps(
            coverage.report(covered=frozenset(map_.values())),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
