"""Structure checks for tasks/install-suse.yml.

- `install_driver` is registered exactly once, so the reboot in
  tasks/main.yml sees one result.
- zypper is only driven through the zypper modules, never command/shell.
- The removal task pins no version (an absent package with a pin fails).
- The kernel module package's availability is checked, in check mode,
  after the CUDA repo is added and before anything is installed.
- A candidate from another branch than the requested one is refused before
  the module task changes anything.
- A branch or version pin older than the installed module is refused
  before the module task changes anything.
- Replacing an installed module pins `nvidia-common-G07` to the version
  the availability check resolved, so the user space follows the module.
- On the DKMS path the running kernel's headers are installed before the
  module.
- Installed versions are read with `rpm -q`, not `package_facts`, which
  needs the rpm Python bindings on ansible-core before 2.21.
- With the signed module enabled the kernel package is SUSE's
  `-signed-cuda-kmp-<flavour>`; the `-signed-kmp-<flavour>` name also
  matches SUSE's graphics module and would install the wrong driver.

The guard expressions are evaluated with ansible-core's templar (2.19+).

Run: uv run --with pytest --with jinja2 --with pyyaml --with 'ansible-core>=2.19' \
    pytest tests/test_suse_tasks.py
"""

from pathlib import Path

import jinja2
import pytest
import yaml
from ansible.template import Templar, trust_as_template

ROLE = Path(__file__).resolve().parent.parent
TASKS = yaml.safe_load((ROLE / "tasks" / "install-suse.yml").read_text())
VARS = yaml.safe_load((ROLE / "vars" / "main.yml").read_text())
KMP = "nvidia-open-driver-G07-signed-cuda-kmp-default"
FLAVORS = ("default", "64kb", "nvidia64kb")


def _task(name):
    (task,) = [t for t in TASKS if t.get("name") == name]
    return task


def _trusted(values):
    return {k: trust_as_template(v) if isinstance(v, str) else v for k, v in values.items()}


def _templar(task, **variables):
    return Templar(variables={
        **_trusted(VARS),
        "nvidia_driver_package_state": "present",
        "nvidia_driver_package_version": "",
        "nvidia_driver_suse_signed_kmp": True,
        "nvidia_driver_suse_kernel_flavor": "default",
        **variables,
        **_trusted(task.get("vars", {})),
    })


def _condition(templar, condition):
    result = templar.evaluate_conditional(trust_as_template(condition))
    # ansible-core before 2.19 wraps a condition in an if statement.
    wrapped = "{% if " + condition + " %}True{% else %}False{% endif %}"
    assert str(templar.template(trust_as_template(wrapped))) == str(result), condition
    return result


def _assert_result(name, **variables):
    """None when the assert is skipped, else whether it passes."""
    task = _task(name)
    templar = _templar(task, **variables)
    if not all(_condition(templar, w) for w in task["when"]):
        return None
    return all(_condition(templar, c) for c in task["ansible.builtin.assert"]["that"])


def _candidate(stdout):
    task = _task("Read the kernel module version zypper would install")
    expr = task["ansible.builtin.set_fact"]["_suse_kmp_candidate"]
    return _templar(task, _suse_kmp_available={"stdout": stdout}).template(trust_as_template(expr))


def test_install_driver_registered_once():
    registers = [t for t in TASKS if t.get("register") == "install_driver"]
    assert len(registers) == 1


def test_no_zypper_through_command_or_shell():
    for task in TASKS:
        for module in ("command", "shell", "ansible.builtin.command", "ansible.builtin.shell"):
            assert "zypper" not in str(task.get(module, "")), task["name"]


def test_removal_has_no_version_pin():
    (remove,) = [t for t in TASKS if t.get("name") == "Remove driver packages"]
    for name in remove["community.general.zypper"]["name"]:
        assert not any(op in name for op in "=<>"), name


def test_availability_checked_after_repo_before_install():
    names = [t.get("name") for t in TASKS]
    check = names.index("Check the kernel module package is available")
    assert names.index("Add CUDA repo") < check
    assert check < names.index("Install kernel module package")
    assert TASKS[check]["check_mode"] is True


@pytest.mark.parametrize("flavor,accepted", [(f, True) for f in FLAVORS] + [("rt", False)])
def test_platform_check_kernel_flavor(flavor, accepted):
    task = _task("Check the SUSE platform is supported")
    templar = _templar(
        task,
        ansible_facts={"distribution": "SLES", "distribution_major_version": "16"},
        nvidia_driver_suse_kernel_flavor=flavor,
    )
    assert all(_condition(templar, c) for c in task["ansible.builtin.assert"]["that"]) is accepted


def test_removal_covers_every_flavor():
    (remove,) = [t for t in TASKS if t.get("name") == "Remove driver packages"]
    names = remove["community.general.zypper"]["name"]
    for flavor in FLAVORS:
        assert f"nvidia-open-driver-G07-signed-cuda-kmp-{flavor}" in names


def test_downgrade_refused_before_module_changes():
    names = [t.get("name") for t in TASKS]
    check = names.index("Check the installed kernel module is not newer than the request")
    assert names.index("Read the installed kernel module version before install") < check
    assert check < names.index("Install kernel module package")


def test_candidate_branch_checked_before_module_changes():
    names = [t.get("name") for t in TASKS]
    read = names.index("Read the kernel module version zypper would install")
    check = names.index("Check the kernel module candidate is from the requested branch")
    assert names.index("Check the kernel module package is available") < read < check
    assert check < names.index("Install kernel module package")


@pytest.mark.parametrize("stdout,candidate", [
    (f'<solvable type="package" name="{KMP}" edition="595.45.04_k6.12.0_160000.5-1.1" arch="x86_64"/>',
     "595.45.04"),
    ("", ""),
])
def test_candidate_read_from_check_mode_output(stdout, candidate):
    assert _candidate(stdout) == candidate


@pytest.mark.parametrize("candidate,branch,expected", [
    ("595.45.04", "610", False),  # only a lower branch is available
    ("610.57.04", "610", True),
    ("", "610", None),  # nothing to install
])
def test_candidate_branch(candidate, branch, expected):
    result = _assert_result(
        "Check the kernel module candidate is from the requested branch",
        _suse_kmp_candidate=candidate, nvidia_driver_suse_branch=branch)
    assert result is expected


def test_candidate_branch_skipped_with_pin():
    assert _assert_result(
        "Check the kernel module candidate is from the requested branch",
        _suse_kmp_candidate="610.57.04", nvidia_driver_suse_branch="615",
        nvidia_driver_package_version="610.57.04_k6.12.0_160000.5") is None


@pytest.mark.parametrize("pin,branch,expected", [
    ("610.57.04_k6.12.0_160000.5", "615", False),  # older pin
    ("615.71.09_k6.12.0_160000.5", "615", True),  # same pin
    ("615.71.09_k6.12.0_160000.7", "615", True),  # same driver, newer kernel build
    ("620.10.01_k6.12.0_160000.5", "615", True),  # newer pin
    ("615.50.01", "615", False),  # older version in the same branch
    ("", "610", False),  # older branch
    ("", "615", True),
    ("", "620", True),
])
def test_downgrade_guard_with_615_installed(pin, branch, expected):
    result = _assert_result(
        "Check the installed kernel module is not newer than the request",
        _suse_kmp_before={"rc": 0, "stdout_lines": ["615.71.09_k6.12.0_160000.5"]},
        nvidia_driver_package_version=pin, nvidia_driver_suse_branch=branch)
    assert result is expected


def test_downgrade_guard_skipped_without_installed_module():
    assert _assert_result(
        "Check the installed kernel module is not newer than the request",
        _suse_kmp_before={"rc": 1, "stdout_lines": []},
        nvidia_driver_package_version="610.57.04", nvidia_driver_suse_branch="610") is None


def test_module_change_pins_user_space():
    names = [t.get("name") for t in TASKS]
    check = TASKS[names.index("Check the kernel module package is available")]
    install = TASKS[names.index("Install kernel module package")]
    assert check["community.general.zypper"]["name"] == "{{ _suse_kernel_package_request }}"
    assert "nvidia-common-G07=" in install["community.general.zypper"]["name"]


def test_no_package_facts():
    for task in TASKS:
        assert "ansible.builtin.package_facts" not in task, task["name"]


def test_dkms_headers_installed_before_module():
    names = [t.get("name") for t in TASKS]
    headers = names.index("Install kernel headers for the running kernel")
    assert headers < names.index("Install kernel module package")
    assert "not nvidia_driver_suse_signed_kmp | bool" in TASKS[headers]["when"]


@pytest.mark.parametrize("flavor", FLAVORS)
@pytest.mark.parametrize("signed,expected", [
    (True, "nvidia-open-driver-G07-signed-cuda-kmp-{flavor}"),
    (False, "nvidia-open-driver-G07"),
])
def test_kernel_package_name(flavor, signed, expected):
    env = jinja2.Environment()
    env.filters["ternary"] = lambda value, true_val, false_val: true_val if value else false_val
    rendered = env.from_string(VARS["_suse_kernel_package"]).render(
        nvidia_driver_suse_signed_kmp=signed,
        nvidia_driver_suse_kernel_flavor=flavor,
    )
    assert rendered == expected.format(flavor=flavor)
