"""Boolean role variables in `when` conditions accept string values.

`nvidia_driver_ubuntu_install_from_cuda_repo`, `nvidia_driver_persistence_mode_on`
and `nvidia_driver_skip_reboot` arrive as strings when set in an INI inventory
`[group:vars]` section or with `-e name=value`. The conditions apply `| bool`,
as they already do for `nvidia_driver_add_repos`, so `"false"` and `"no"` select
the same tasks as `false`. Without it ansible-core 2.19+ rejects the condition
("Conditionals must have a boolean result") and older releases treat any
non-empty string as true.

The conditions are read from the task files and evaluated with ansible-core's
templar (2.19+), and in the `{% if %}` form older releases used.

Run: uv run --with pytest --with jinja2 --with pyyaml --with 'ansible-core>=2.19' \
    pytest tests/test_boolean_vars.py
"""

from pathlib import Path

import pytest
import yaml
from ansible.template import Templar, trust_as_template

ROLE = Path(__file__).resolve().parent.parent
MAIN = yaml.safe_load((ROLE / "tasks" / "main.yml").read_text())
REDHAT = yaml.safe_load((ROLE / "tasks" / "install-redhat.yml").read_text())

# (value as set by the user, intended boolean)
VALUES = [
    (True, True),
    (False, False),
    ("true", True),
    ("false", False),
    ("yes", True),
    ("no", False),
]


def _when(tasks, name):
    (task,) = [t for t in tasks if t.get("name") == name]
    return task["when"]


def _rescue_reboot_when():
    (block,) = [t for t in REDHAT if "rescue" in t]
    (task,) = [t for t in block["rescue"] if "reboot" in t]
    return task["when"]


def _runs(condition, **variables):
    templar = Templar(variables={
        "ansible_facts": {"distribution": "Ubuntu", "os_family": "Debian"},
        "install_driver": {"changed": True},
        **variables,
    })
    result = templar.evaluate_conditional(trust_as_template(condition))
    # ansible-core before 2.19 wraps a condition in an if statement.
    wrapped = "{% if " + condition + " %}True{% else %}False{% endif %}"
    assert str(templar.template(trust_as_template(wrapped))) == str(result), condition
    return result


@pytest.mark.parametrize("value,enabled", VALUES)
def test_ubuntu_install_path(value, enabled):
    canonical = _when(MAIN, "ubuntu install tasks (canonical repos)")
    cuda = _when(MAIN, "ubuntu install tasks (CUDA repo)")
    variables = {"nvidia_driver_ubuntu_install_from_cuda_repo": value}
    assert _runs(canonical, **variables) is not enabled
    assert _runs(cuda, **variables) is enabled


@pytest.mark.parametrize("value,enabled", VALUES)
def test_persistence_mode_override(value, enabled):
    add = _when(MAIN, "configure persistenced service to turn on persistence mode")
    remove = _when(MAIN, "remove persistenced service override")
    variables = {"nvidia_driver_persistence_mode_on": value}
    assert _runs(add, **variables) is enabled
    assert _runs(remove, **variables) is not enabled


@pytest.mark.parametrize("value,skip", VALUES)
def test_skip_reboot(value, skip):
    variables = {"nvidia_driver_skip_reboot": value}
    assert _runs(_when(MAIN, "reboot after driver install"), **variables) is not skip
    assert _runs(_rescue_reboot_when(), **variables) is not skip
