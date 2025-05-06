# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from unimnim import coverage


def test_report() -> None:
    report = coverage.report(covered={"a"})

    assert report["en"]["total"] > 26 * 2
    assert report["en"]["covered_count"] == 1
    assert report["en"]["missing_count"] == report["en"]["total"] - 1
    assert "a" not in report["en"]["missing"]
    assert len(report["en"]["missing"]) == report["en"]["missing_count"]
