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

    script = report["script"]
    assert script["Latn"]["total"] > 26 * 2
    assert script["Latn"]["covered_count"] == 1
