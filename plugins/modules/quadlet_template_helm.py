#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: quadlet_template_helm
short_description: Render Helm chart and deploy as Podman quadlet manifest
description:
  - Renders a Helm chart using C(kubernetes.core.helm_template) on the controller
  - Deploys the rendered manifest to a destination directory on the target
  - Output file is named C(<name>.yaml) inside the destination directory
  - Supports C(state=absent) to remove previously deployed manifests
version_added: "1.0.0"
options:
  chart:
    description:
      - Path to the Helm chart directory
      - Resolved relative to the playbook file directory if not absolute
      - Required when C(state=present)
    required: false
    type: str
  dest:
    description:
      - Destination directory for the rendered manifest on the target
      - Output file will be named C(<name>.yaml) inside this directory
    required: true
    type: str
  name:
    description:
      - Release name passed to C(helm template)
      - Also used as the output filename (C(<name>.yaml))
    required: true
    type: str
  state:
    description:
      - C(present) renders the chart and deploys the manifest
      - C(absent) removes the manifest file from the destination
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
  values_files:
    description:
      - List of values files to pass to C(helm template)
      - Resolved relative to the playbook file directory if not absolute
      - Evaluated before C(values) and C(set_values)
    required: false
    type: list
    elements: str
    default: []
  values:
    description:
      - Dictionary of values to pass to C(helm template)
      - Mapped to C(release_values) in C(kubernetes.core.helm_template)
      - Evaluated after C(values_files) but before C(set_values)
    required: false
    type: dict
    default: {}
  set_values:
    description:
      - List of individual values to set with type control
      - Highest precedence — overrides both C(values_files) and C(values)
    required: false
    type: list
    elements: dict
    default: []
    suboptions:
      value:
        description: Value expression (e.g., C(phase=prod))
        required: true
        type: str
      value_type:
        description:
          - C(raw) - direct interpolation
          - C(string) - force string type
          - C(json) - JSON values (requires helm >= 3.10.0)
          - C(file) - load value from file
        type: str
        choices: ['raw', 'string', 'json', 'file']
        default: raw
  namespace:
    description:
      - Namespace scope for the release
    required: false
    type: str
  include_crds:
    description:
      - Include CRDs in rendered output
    required: false
    type: bool
    default: false
  binary_path:
    description:
      - Path to a custom helm binary
      - Passed directly to C(kubernetes.core.helm_template)
    required: false
    type: path
author:
  - cenk1cenk2
notes:
  - Helm runs on the controller via a LocalConnection swap, not on the target
  - Requires the C(kubernetes.core) collection and C(helm) binary on the controller
  - Chart and values_files paths are resolved relative to the playbook file directory
  - The manifest is deployed to the target via C(ansible.builtin.copy)
"""

EXAMPLES = r"""
- name: Render and deploy a chart
  cenk1cenk2.reloaded.quadlet_template_helm:
    chart: ./files/charts/myapp
    dest: '{{ podman_kube_quadlet_dir }}'
    name: myapp
    values:
      timezone: '{{ local_timezone }}'
  register: manifest

- name: Use the filename in podman_play
  containers.podman.podman_play:
    state: quadlet
    quadlet_dir: '{{ podman_kube_quadlet_dir }}'
    quadlet_filename: myapp
    kube_file: './{{ manifest.filename }}'

- name: Render with values files and overrides
  cenk1cenk2.reloaded.quadlet_template_helm:
    chart: ./files/charts/myapp
    dest: '{{ podman_kube_quadlet_dir }}'
    name: myapp
    values_files:
      - ./files/values/base.yml
      - ./files/values/prod.yml
    values:
      image:
        tag: v1.2.3

- name: Remove a manifest
  cenk1cenk2.reloaded.quadlet_template_helm:
    dest: '{{ podman_kube_quadlet_dir }}'
    name: myapp
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the manifest file was created, modified, or removed
  returned: always
  type: bool
dest:
  description: Full path to the manifest file
  returned: always
  type: str
  sample: /etc/containers/systemd/myapp.yaml
filename:
  description: Just the manifest filename without directory path
  returned: when state is 'present'
  type: str
  sample: myapp.yaml
manifest:
  description: The rendered manifest content
  returned: when state is 'present'
  type: str
command:
  description: The helm command that was executed
  returned: when state is 'present'
  type: str
diff:
  description: File diff from the copy action
  returned: when diff mode is enabled and file changed
  type: dict
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
