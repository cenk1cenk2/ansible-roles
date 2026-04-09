#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: quadlet_systemd
short_description: Reload systemd and manage quadlet service states
description:
  - Runs systemd daemon_reload then sets service states
  - Supports trigger-based restart logic for quadlet services
  - When state is C(reloaded) (default) and any trigger is true, the service is restarted
  - When state is C(reloaded) and no triggers fired, the service is started
  - Other states (started, stopped, restarted) are passed through directly
version_added: "1.0.0"
options:
  services:
    description:
      - List of services to manage
      - Each item can be a string (service name) or a dict with C(name), optional C(state), and optional C(scope)
    required: true
    type: list
    elements: raw
  triggers:
    description:
      - List of booleans indicating whether upstream tasks changed
      - If any trigger is true and service state is C(reloaded), service will be restarted
    required: false
    type: list
    elements: bool
    default: []
  scope:
    description:
      - Default systemd scope for all services
      - Can be overridden per service
    required: false
    type: str
    default: system
author:
  - cenk1cenk2
notes:
  - This is an action plugin that delegates to ansible.builtin.systemd
  - Always runs daemon_reload before managing services
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
"""

RETURN = r"""
changed:
  description: Whether any service state changed
  returned: always
  type: bool
services:
  description: List of services processed with their resolved state and changed status
  returned: always
  type: list
  elements: dict
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
