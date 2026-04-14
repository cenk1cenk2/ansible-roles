#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: quadlet_systemd
short_description: Reload systemd and manage quadlet service states
description:
  - Runs systemd C(daemon_reload) then manages service states
  - Supports trigger-based restart logic for quadlet services
  - When service state is C(reloaded) (default) and any trigger is true, the service is restarted
  - When service state is C(reloaded) and no triggers fired, the service is started
  - Other states (C(started), C(stopped), C(restarted)) are passed through directly
version_added: "1.0.0"
options:
  services:
    description:
      - List of services to manage
      - Each item can be a string (service name) or a dict with C(name), optional C(state), and optional C(scope)
      - Default state is C(reloaded) which resolves to C(started) or C(restarted) based on triggers
    required: true
    type: list
    elements: raw
    suboptions:
      name:
        description: Systemd service unit name (e.g., C(myapp.service))
        required: true
        type: str
      state:
        description:
          - Desired service state
          - C(reloaded) resolves to C(started) or C(restarted) based on triggers
          - Other values are passed directly to systemd
        type: str
        choices: ['reloaded', 'started', 'stopped', 'restarted']
        default: reloaded
      scope:
        description: Systemd scope override for this service (overrides task-level C(scope))
        type: str
  triggers:
    description:
      - List of booleans indicating whether upstream tasks changed
      - If any trigger is true and service state is C(reloaded), the service is restarted instead of started
      - Typically fed from C(.changed) of upstream task results
    required: false
    type: list
    elements: bool
    default: []
  scope:
    description:
      - Default systemd scope for all services
      - Can be overridden per service via the service dict's C(scope) key
    required: false
    type: str
    default: system
author:
  - cenk1cenk2
notes:
  - This is an action plugin that delegates to C(ansible.builtin.systemd)
  - Always runs C(daemon_reload) before managing services
  - Services can override the default scope individually
"""

EXAMPLES = r"""
- name: Reload and restart services if changed
  cenk1cenk2.reloaded.quadlet_systemd:
    triggers:
      - '{{ manifest_result.changed }}'
      - '{{ quadlet_result.changed }}'
    services:
      - name: myapp.service

- name: Simple service list as strings
  cenk1cenk2.reloaded.quadlet_systemd:
    services:
      - myapp.service
      - mydb.service

- name: Mixed states
  cenk1cenk2.reloaded.quadlet_systemd:
    services:
      - name: myapp.service
        state: restarted
      - name: mydb.service
        state: started

- name: User scope services
  cenk1cenk2.reloaded.quadlet_systemd:
    scope: user
    triggers:
      - '{{ result.changed }}'
    services:
      - name: myapp.service
"""

RETURN = r"""
changed:
  description: Whether any service state changed
  returned: always
  type: bool
triggered:
  description: Whether any trigger was true
  returned: always
  type: bool
services:
  description: List of services processed with their resolved state and changed status
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Service unit name
      type: str
      sample: myapp.service
    state:
      description: Resolved state that was applied
      type: str
      sample: restarted
    changed:
      description: Whether this specific service changed
      type: bool
msg:
  description: Human-readable result message
  returned: always
  type: str
  sample: "Processed myapp.service (triggered=True)"
"""
