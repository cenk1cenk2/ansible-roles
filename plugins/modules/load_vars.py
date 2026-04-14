#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: load_vars
short_description: Load variables from files with pattern or environment modes
description:
  - Loads variables from YAML/JSON files using glob patterns or hierarchical environment structure
  - Supports two modes - C(pattern) for glob-based loading and C(environment) for hierarchical loading
  - Variables can be injected globally as facts or returned locally via the C(scope) parameter
  - Returns per-file data in C(files) for iteration patterns
version_added: "1.0.0"
options:
  mode:
    description:
      - Loading mode to use
      - C(pattern) - Load all files matching a glob pattern from root directory
      - C(environment) - Load common variables first, then environment-specific variables
    required: true
    type: str
    choices: ['pattern', 'environment']
  root:
    description:
      - Base directory path for file loading
      - Resolved relative to the playbook file directory if not absolute
    required: true
    type: str
  pattern:
    description:
      - Glob pattern to match files (e.g., C(*.yml), C(vars_*.yaml))
      - If pattern has no extension, C(.yml), C(.yaml), and C(.json) are appended automatically
      - Required when mode is C(pattern)
    required: false
    type: str
  environment:
    description:
      - Environment name for hierarchical loading (e.g., C(prod), C(dev), C(staging))
      - Required when mode is C(environment)
    required: false
    type: str
  common:
    description:
      - Common directory name for shared variables in environment mode
      - Only used when mode is C(environment)
    required: false
    type: str
    default: base
  strict:
    description:
      - Whether to fail when no files match
      - When C(true), plugin fails if no files are found
      - When C(false), plugin succeeds with empty results and a warning
    required: false
    type: bool
    default: false
  hash_behaviour:
    description:
      - How to merge loaded variables across files
      - C(replace) - Later files overwrite entire values from earlier files
      - C(merge) - Deep merge dictionaries so nested keys from earlier files are preserved
      - Defaults to the global C(DEFAULT_HASH_BEHAVIOUR) setting
    required: false
    type: str
    choices: ['replace', 'merge']
  scope:
    description:
      - Controls how loaded variables are registered
      - C(global) - Injects variables as host facts (accessible as C(ansible_facts.*) or top-level vars)
      - C(return) - Returns variables under C(vars) key without injecting into host scope. Use with C(register) for loop patterns
    required: false
    type: str
    choices: ['global', 'return']
    default: global
author:
  - cenk1cenk2
notes:
  - This is an action plugin that runs on the controller
  - Files are loaded in sorted order for deterministic behavior
  - In environment mode, environment-specific variables override common variables
  - Supports C(.yml), C(.yaml), and C(.json) files
  - With C(scope=return), uses direct YAML loading instead of C(include_vars) to avoid fact injection
"""

EXAMPLES = r"""
- name: Load variables by pattern (global scope)
  cenk1cenk2.reloaded.load_vars:
    mode: pattern
    root: ./vars
    pattern: "*.yml"

- name: Load environment variables (common + prod)
  cenk1cenk2.reloaded.load_vars:
    mode: environment
    root: ./vars
    environment: '{{ inventory_hostname }}'

- name: Load instance files for iteration (return scope)
  cenk1cenk2.reloaded.load_vars:
    mode: pattern
    root: './vars/{{ inventory_hostname }}/instances'
    pattern: '*.yml'
    scope: return
  register: instances

- name: Loop over discovered instances
  ansible.builtin.include_tasks: ./tasks/instance.yml
  loop: '{{ instances.files }}'
  loop_control:
    loop_var: instance

- name: Deep merge variables across files
  cenk1cenk2.reloaded.load_vars:
    mode: pattern
    root: ./vars
    pattern: "*.yml"
    hash_behaviour: merge
"""

RETURN = r"""
loaded_files:
  description: List of files that were successfully loaded
  returned: always
  type: list
  elements: str
  sample: ['/path/to/vars/base/common.yml', '/path/to/vars/prod/app.yml']
variables_loaded:
  description: Number of unique top-level variables loaded
  returned: always
  type: int
  sample: 7
root:
  description: Resolved root directory path
  returned: always
  type: str
  sample: /home/user/playbooks/vars
matched_files:
  description: All files matching the glob pattern (before loading)
  returned: when mode is 'pattern'
  type: list
  elements: str
files:
  description: Per-file data with filename, path, and parsed content
  returned: always
  type: list
  elements: dict
  contains:
    filename:
      description: Base filename
      type: str
      sample: common.yml
    path:
      description: Full file path
      type: str
      sample: /path/to/vars/base/common.yml
    data:
      description: Parsed YAML content of the file
      type: dict
vars:
  description: Merged variables from all loaded files (only when scope is 'return')
  returned: when scope is 'return'
  type: dict
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
