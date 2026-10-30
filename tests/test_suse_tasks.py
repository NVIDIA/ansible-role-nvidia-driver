"""Structure checks for tasks/install-suse.yml.

- `install_driver` is registered exactly once, so the reboot in
  tasks/main.yml sees one result.
- zypper is only driven through the zypper modules, never command/shell.
- The removal task pins no version (an absent package with a pin fails).
- The kernel module package's availability is checked, in check mode,
  after the CUDA repo is added and before anything is installed.
- A branch older than the installed module is refused before the module
  task changes anything.
- On the DKMS path the running kernel's headers are installed before the
  module.
- Installed versions are read with `rpm -q`, not `package_facts`, which
  needs the rpm Python bindings on ansible-core before 2.21.
- With the signed module enabled the kernel package is SUSE's
  `-signed-cuda-kmp-<flavour>`; the `-signed-kmp-<flavour>` name also
  matches SUSE's graphics module and would install the wrong driver.

Run: uv run --with pytest --with jinja2 --with pyyaml pytest tests/test_suse_tasks.py
"""

from pathlib import Path

import jinja2
import pytest
import yaml

ROLE = Path(__file__).resolve().parent.parent
TASKS = yaml.safe_load((ROLE / "tasks" / "install-suse.yml").read_text())
VARS = yaml.safe_load((ROLE / "vars" / "main.yml").read_text())


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


def test_removal_covers_every_flavor():
    (remove,) = [t for t in TASKS if t.get("name") == "Remove driver packages"]
    names = remove["community.general.zypper"]["name"]
    for flavor in ("default", "64kb", "nvidia"):
        assert f"nvidia-open-driver-G07-signed-cuda-kmp-{flavor}" in names


def test_downgrade_refused_before_module_changes():
    names = [t.get("name") for t in TASKS]
    check = names.index("Check the installed kernel module is not from a newer branch")
    assert names.index("Read the installed kernel module version before install") < check
    assert check < names.index("Install kernel module package")


def test_no_package_facts():
    for task in TASKS:
        assert "ansible.builtin.package_facts" not in task, task["name"]


def test_dkms_headers_installed_before_module():
    names = [t.get("name") for t in TASKS]
    headers = names.index("Install kernel headers for the running kernel")
    assert headers < names.index("Install kernel module package")
    assert "not nvidia_driver_suse_signed_kmp | bool" in TASKS[headers]["when"]


@pytest.mark.parametrize("flavor", ["default", "64kb", "nvidia"])
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
