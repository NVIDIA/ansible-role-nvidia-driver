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


| Variable | Default value | Description |
| -------- | ------------- | ----------- |
| `nvidia_driver_package_state` | `"present"` | Package state for NVIDIA driver packages |
| `nvidia_driver_package_version` | `""` | Package version to install. Note that this should match the actual version of the deb or RPM package to be installed. |
| `nvidia_driver_persistence_mode_on` | `yes` | Whether to enable persistence mode (boolean) |
| `nvidia_driver_skip_reboot` | `no` | Whether to skip rebooting the node during the install |
| `nvidia_driver_module_file` | `"/etc/modprobe.d/nvidia.conf"` | Filename to use for NVIDIA driver parameters |
| `nvidia_driver_module_params` | `""` | Parameters to pass to the NVIDIA driver |
| `nvidia_driver_branch` | `"510"` | Default driver branch to install |

### Red Hat specific variables


| Variable | Default value | Description |
| -------- | ------------- | ----------- |
| `epel_package` | `"https://dl.fedoraproject.org/pub/epel/epel-release-latest-{{ ansible_distribution_major_version }}.noarch.rpm"` | Package to install to enable EPEL |
| `nvidia_driver_rhel_cuda_repo_baseurl` | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _rhel_repo_dir }}/"` | Base URL to use for CUDA repo |
| `nvidia_driver_rhel_cuda_repo_gpgkey` | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _rhel_repo_dir }}/7fa2af80.pub"` | GPG key for the CUDA repo |

### Ubuntu specific variables

For Ubuntu installs, you have the choice of installing from the Canonical repositories and the NVIDIA CUDA repositories.

By default, the Canonical repositories will be used, and the driver installed will be the headless server driver.

| Variable | Default value | Description |
| -------- | ------------- | ----------- |
| `nvidia_driver_ubuntu_install_from_cuda_repo` | `no` | Flag whether to use the CUDA repo |
| `nvidia_driver_ubuntu_cuda_repo_baseurl` | `"http://developer.download.nvidia.com/compute/cuda/repos/{{ _ubuntu_repo_dir }}"` | Base URL to use for CUDA repo |
| `nvidia_driver_ubuntu_cuda_package` | `"cuda-drivers"` | Package name to install from CUDA repo |

## Example playbook

```
- hosts: gpu_nodes
  roles:
  - nvidia.nvidia_driver
```

## Supported distributions

Currently, this role supports the following Linux distributions:

* NVIDIA DGX OS 4
* NVIDIA DGX OS 5
* Ubuntu 18.04 LTS
* Ubuntu 20.04 LTS
* CentOS 7
* Red Hat Enterprise Linux 7
* CentOS 8
* Red Hat Enterprise Linux 8
