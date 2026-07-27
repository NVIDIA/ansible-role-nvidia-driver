# ansible-role-nvidia-driver

An Ansible role to install the NVIDIA driver from the NVIDIA CUDA repositories.

## Requirements

In the process of installing the NVIDIA driver, this role will reboot the nodes where it runs.
Because of this, we strongly recommend that you run `ansible-playbook` from a separate node than the GPU nodes where you are installing the driver.

If you attempt to run Ansible on the same node where you are installing the driver, this role will either:

* Refuse to proceed with an error like `Running reboot with local connection would reboot the control node` (if running with the `local` connection)
* Reboot the node you're running on, interrupting the playbook execution! (if running the an `ssh` connection against localhost)

## Installing

This role can be installed using [Ansible Galaxy](https://galaxy.ansible.com/nvidia/nvidia_driver):

```
$ ansible-galaxy install nvidia.nvidia_driver
```

## Role variables


| Variable                            | Default value                   | Description                                                                                                           |
|-------------------------------------|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `nvidia_driver_package_state`       | `"present"`                     | Package state for NVIDIA driver packages                                                                              |
| `nvidia_driver_package_version`     | `""`                            | Package version to install. Note that this should match the actual version of the deb or RPM package to be installed. |
| `nvidia_driver_persistence_mode_on` | `yes`                           | Whether to enable persistence mode (boolean)                                                                          |
| `nvidia_driver_skip_reboot`         | `no`                            | Whether to skip rebooting the node during the install                                                                 |
| `nvidia_driver_module_file`         | `"/etc/modprobe.d/nvidia.conf"` | Filename to use for NVIDIA driver parameters                                                                          |
| `nvidia_driver_module_params`       | `""`                            | Parameters to pass to the NVIDIA driver                                                                               |
| `nvidia_driver_branch`              | `"515"`                         | Default driver branch to install                                                                                      |

### Red Hat specific variables


| Variable                               | Default value                                                                                                     | Description                       |
|----------------------------------------|-------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| `epel_package`                         | `"https://dl.fedoraproject.org/pub/epel/epel-release-latest-{{ ansible_distribution_major_version }}.noarch.rpm"` | Package to install to enable EPEL |
| `nvidia_driver_rhel_cuda_repo_baseurl` | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _rhel_repo_dir }}/"`                                | Base URL to use for CUDA repo     |
| `nvidia_driver_rhel_cuda_repo_gpgkey`  | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _rhel_repo_dir }}/7fa2af80.pub"`                    | GPG key for the CUDA repo         |

### Ubuntu specific variables

For Ubuntu installs, you have the choice of installing from the Canonical repositories and the NVIDIA CUDA repositories.

By default, the Canonical repositories will be used, and the driver installed will be the headless server driver.

| Variable                                      | Default value                                                                      | Description                                          |
|-----------------------------------------------|------------------------------------------------------------------------------------|------------------------------------------------------|
| `nvidia_driver_ubuntu_install_from_cuda_repo` | `no`                                                                               | Flag whether to use the CUDA repo                    |
| `nvidia_driver_ubuntu_cuda_repo_baseurl`      | `"http://developer.download.nvidia.com/compute/cuda/repos/{{ _ubuntu_repo_dir }}"` | Base URL to use for CUDA repo                        |
| `nvidia_driver_ubuntu_cuda_package`           | `"cuda-drivers"`                                                                   | Package name to install from CUDA repo               |
| `nvidia_driver_ubuntu_packages_suffix`        | `"-server"`                                                                        | The suffix added to the apt packages when installing |

## Example playbook

```
- hosts: gpu_nodes
  roles:
  - nvidia.nvidia_driver
```

## Ansible collection dependency

This role uses modules from the `community.general` collection, which is not
part of `ansible-core`. When installing the role from Galaxy, install the
collection explicitly:

```
ansible-galaxy collection install community.general
```

For a source checkout, `ansible-galaxy collection install -r requirements.yml`
installs the declared collection dependencies.

## Supported distributions

Currently exercised by Molecule's container CI:

* Ubuntu 22.04 LTS
* Ubuntu 24.04 LTS
* Rocky Linux 8
* Rocky Linux 9

Red Hat Enterprise Linux 8 and 9 use the same Red Hat-family role path and
NVIDIA repositories as the Rocky Linux scenarios, but RHEL itself is not
directly exercised in CI.

NVIDIA DGX OS 6 and DGX OS 7 are based on Ubuntu 22.04 and Ubuntu 24.04
respectively. They share the Ubuntu role paths, but DGX OS and physical DGX
hardware are not directly exercised in CI.

The role retains legacy code paths for the following. They are not exercised
in CI and receive best-effort, community support; users should verify
repository and driver availability for their target release.

* NVIDIA DGX OS 4 / DGX OS 5
* Ubuntu 18.04 LTS / Ubuntu 20.04 LTS
* CentOS 7 / Red Hat Enterprise Linux 7
* CentOS 8
