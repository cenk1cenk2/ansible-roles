#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: quadlet_template_helm
short_description: Render Helm chart and deploy as Podman quadlet manifest
description:
  - Renders a Helm chart using kubernetes.core.helm_template
  - Deploys the rendered manifest to a destination directory for use with Podman quadlet
  - Supports values files, inline values, and set_values for chart configuration
version_added: "1.0.0"
options:
  chart:
    description:
      - Path to the Helm chart directory
      - Resolved relative to the playbook directory if not absolute
    required: true
    type: str
  dest:
    description:
      - Destination directory for the rendered manifest
      - Output file will be named C(<name>.yml) inside this directory
    required: true
    type: str
  name:
    description:
      - Release name passed to helm template
      - Also used as the output filename
    required: true
    type: str
  values_files:
    description:
      - List of values files to pass to helm template
      - Resolved relative to the playbook directory if not absolute
      - Evaluated before C(values) and C(set_values)
    required: false
    type: list
    elements: str
    default: []
  values:
    description:
      - Dictionary of values to pass to helm template
      - Mapped to C(release_values) in kubernetes.core.helm_template
      - Evaluated after C(values_files) but before C(set_values)
    required: false
    type: dict
    default: {}
  set_values:
    description:
      - List of individual values to set with type control
      - Each item has C(value) (required) and C(value_type) (raw/string/json/file)
      - Highest precedence
    required: false
    type: list
    elements: dict
    default: []
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
author:
  - cenk1cenk2
notes:
  - This is an action plugin that runs on the controller
  - Requires the kubernetes.core collection and helm binary
  - Chart paths are resolved relative to the playbook directory
"""

EXAMPLES = r"""
- name: Render and deploy a chart
  cenk1cenk2.reloaded.quadlet_template_helm:
    chart: ./files/charts/myapp
    dest: /etc/containers/systemd
    name: myapp

- name: Render with values files and overrides
  cenk1cenk2.reloaded.quadlet_template_helm:
    chart: ./files/charts/myapp
    dest: /etc/containers/systemd
    name: myapp
    values_files:
      - ./files/values/base.yml
      - ./files/values/prod.yml
    values:
      image:
        tag: v1.2.3
    set_values:
      - value: "replicas=3"
        value_type: raw
"""

RETURN = r"""
changed:
  description: Whether the manifest file was created or modified
  returned: always
  type: bool
dest:
  description: Full path to the deployed manifest file
  returned: always
  type: str
  sample: /etc/containers/systemd/myapp.yml
manifest:
  description: The rendered manifest content
  returned: always
  type: str
command:
  description: The helm command that was executed
  returned: always
  type: str
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
