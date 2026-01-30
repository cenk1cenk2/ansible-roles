#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: load_vars
short_description: Load variables from files with pattern or environment modes
description:
  - Loads variables from YAML/JSON files using glob patterns or hierarchical environment structure
  - Supports two modes - 'pattern' for glob-based loading and 'environment' for hierarchical loading
  - Returns structured output with loaded files list and variable counts
  - Provides enhanced logging at multiple verbosity levels
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
      - All file paths will be relative to this directory
    required: true
    type: str
  pattern:
    description:
      - Glob pattern to match files (e.g., C(*.yml), C(vars_*.yaml))
      - Required when mode is C(pattern)
      - Ignored when mode is C(environment)
    required: false
    type: str
  environment:
    description:
      - Environment name for hierarchical loading (e.g., C(prod), C(dev), C(staging))
      - Required when mode is C(environment)
      - Ignored when mode is C(pattern)
    required: false
    type: str
  common:
    description:
      - Common directory name for shared variables in environment mode
      - Defaults to C(base) if not specified
      - Only used when mode is C(environment)
    required: false
    type: str
    default: base
  strict:
    description:
      - Whether to fail when no files match the pattern or environment structure
      - When C(true), plugin fails if no files are found
      - When C(false), plugin succeeds with empty list and warning
    required: false
    type: bool
    default: false
author:
  - Ansible Project
notes:
  - This module is actually an action plugin and will always execute on the controller
  - Files are loaded in sorted order for deterministic behavior
  - In environment mode, environment-specific variables override common variables
  - Supports YAML and JSON variable files
'''

EXAMPLES = r'''
- name: Load variables by pattern
  cenk1cenk2.reloaded.load_vars:
    mode: pattern
    root: /path/to/vars
    pattern: "*.yml"

- name: Load variables by pattern with strict mode
  cenk1cenk2.reloaded.load_vars:
    mode: pattern
    root: /path/to/vars
    pattern: "config_*.yaml"
    strict: true

- name: Load environment variables (common + prod)
  cenk1cenk2.reloaded.load_vars:
    mode: environment
    root: /path/to/vars
    environment: prod
    common: base

- name: Load environment variables with default common directory
  cenk1cenk2.reloaded.load_vars:
    mode: environment
    root: /path/to/vars
    environment: staging

- name: Load environment variables with strict mode
  cenk1cenk2.reloaded.load_vars:
    mode: environment
    root: /path/to/vars
    environment: dev
    strict: true
'''

RETURN = r'''
loaded_files:
  description: List of files that were loaded
  returned: always
  type: list
  elements: str
  sample: ['/path/to/vars/base/common.yml', '/path/to/vars/prod/app.yml']
variables_loaded:
  description: Number of variables loaded from all files
  returned: always
  type: int
  sample: 42
msg:
  description: Human-readable message describing the result
  returned: always
  type: str
  sample: "Loaded 42 variables from 2 files"
failed:
  description: Whether the task failed
  returned: always
  type: bool
  sample: false
'''
