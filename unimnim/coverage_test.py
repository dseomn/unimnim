# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from unimnim import coverage


def test_report() -> None:
    report = coverage.report(covered={"a"})

    language = report["language"]
    assert language["en"]["total"] > 26 * 2
    assert language["en"]["covered_count"] == 1
    assert language["en"]["missing_count"] == language["en"]["total"] - 1
    assert "a" not in language["en"]["missing"]
    assert len(language["en"]["missing"]) == language["en"]["missing_count"]

    script_all = report["scriptAll"]
    assert script_all["Latn"]["total"] > 26 * 2
    assert script_all["Latn"]["covered_count"] == 1

    script_exemplar = report["scriptExemplar"]
    assert script_exemplar["Latn"]["total"] > 26 * 2
    assert script_exemplar["Latn"]["covered_count"] == 1
