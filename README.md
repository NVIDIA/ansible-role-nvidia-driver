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
| `nvidia_driver_major_package_version` | `""` | Major version to install. e.g. 450. |
| `nvidia_driver_package_version` | `""` | Package version to install. Note that this should match the actual version of the deb or RPM package to be installed. |
| `nvidia_driver_persistence_mode_on` | `yes` | Whether to enable persistence mode (boolean) |
| `nvidia_driver_skip_reboot` | `no` | Whether to skip rebooting the node during the install |
| `nvidia_driver_module_file` | `"/etc/modprobe.d/nvidia.conf"` | Filename to use for NVIDIA driver parameters |
| `nvidia_driver_module_params` | `""` | Parameters to pass to the NVIDIA driver |

### Red Hat specific variables


| Variable | Default value | Description |
| -------- | ------------- | ----------- |
| `nvidia_driver_rhel_epel_repo_baseurl` | `"https://download.fedoraproject.org/pub/epel/$releasever/$basearch/"` | Base URL to use for EPEL repo |
| `nvidia_driver_rhel_epel_repo_gpgkey` | `"https://epel.mirror.constant.com//RPM-GPG-KEY-EPEL-{{ ansible_distribution_major_version }}"` | GPG key for the EPEL repo |
| `nvidia_driver_rhel_cuda_repo_baseurl` | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _rhel_repo_dir }}/"` | Base URL to use for CUDA repo |
| `nvidia_driver_rhel_cuda_repo_gpgkey` | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _rhel_repo_dir }}/7fa2af80.pub"` | GPG key for the CUDA repo |

### Ubuntu specific variables


| Variable | Default value | Description |
| -------- | ------------- | ----------- |
| `nvidia_driver_ubuntu_cuda_repo_baseurl` | `"http://developer.download.nvidia.com/compute/cuda/repos/{{ _ubuntu_repo_dir }}"` | Base URL to use for CUDA repo |
| `nvidia_driver_ubuntu_cuda_repo_gpgkey_url` | `"https://developer.download.nvidia.com/compute/cuda/repos/{{ _ubuntu_repo_dir }}/7fa2af80.pub"` | GPG key for the CUDA repo |
| `nvidia_driver_ubuntu_cuda_repo_gpgkey_id` | `"7fa2af80"` | GPG key ID for the CUDA repo |

## Example playbook

```
- hosts: gpu_nodes
  roles:
  - nvidia.nvidia_driver
```

## Supported distributions

Currently, this role supports the following Linux distributions:

* NVIDIA DGX OS 4
* Ubuntu 18.04 LTS
* CentOS 7
* Red Hat Enterprise Linux 7
