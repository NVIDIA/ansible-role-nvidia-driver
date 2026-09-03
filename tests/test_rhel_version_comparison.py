"""Regression test: RHEL major-version comparisons in tasks/install-redhat.yml.

Bug: the version-gated `when` conditions compared the string fact
`ansible_facts['distribution_major_version']` against string literals, so Jinja
performed a lexicographic comparison. For major version '10',
`'10' < '8'` is True and `'10' > '7'` is False, which would run the
legacy RHEL-7 yum task and skip the modern dnf task.

Fix: cast the fact with `| int` before comparing.

This test extracts the two version-gated `when` expressions from the
tasks file and evaluates them with Jinja2 (the same engine Ansible
uses) for major versions 7/8/9/10, asserting that EL10 selects the
RHEL-8 (dnf) path.

Run: uv run --with pytest --with jinja2 --with pyyaml pytest tests/test_rhel_version_comparison.py
"""

from pathlib import Path

import jinja2
import pytest
import yaml

TASKS_FILE = Path(__file__).resolve().parent.parent / "tasks" / "install-redhat.yml"

# (version, expect_el7_task, expect_el8_task)
EXPECTED = [
    ("7", True, False),
    ("8", False, True),
    ("9", False, True),
    ("10", False, True),  # the case the string comparison got wrong
]


TASK_NAMES = (
    "install driver packages RHEL/CentOS 7 and older",
    "install driver packages RHEL/CentOS 8 and newer",
)


def _version_conditions():
    """Return (el7_when, el8_when) expressions from the tasks file."""
    tasks = yaml.safe_load(TASKS_FILE.read_text())
    by_name = {task.get("name"): task.get("when") for task in tasks}
    conditions = [by_name.get(name) for name in TASK_NAMES]
    assert all(isinstance(c, str) for c in conditions), (
        f"expected version-gated when conditions for {TASK_NAMES!r}, found {conditions!r}"
    )
    return conditions


@pytest.mark.parametrize("version,expect_el7,expect_el8", EXPECTED)
def test_driver_install_task_selection(version, expect_el7, expect_el8):
    el7_when, el8_when = _version_conditions()
    env = jinja2.Environment()
    run_el7 = env.compile_expression(el7_when)(
        ansible_facts={'distribution_major_version': version}
    )
    run_el8 = env.compile_expression(el8_when)(
        ansible_facts={'distribution_major_version': version}
    )
    assert bool(run_el7) is expect_el7, (
        f"EL{version}: legacy yum task condition {el7_when!r} "
        f"evaluated to {run_el7}, expected {expect_el7}"
    )
    assert bool(run_el8) is expect_el8, (
        f"EL{version}: modern dnf task condition {el8_when!r} "
        f"evaluated to {run_el8}, expected {expect_el8}"
    )
