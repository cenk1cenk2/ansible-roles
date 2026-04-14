#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: copy_files
short_description: Copy files from a source directory tree to a destination
description:
  - Scans a source directory on the controller and copies files to the target preserving structure
  - Automatically categorizes files by naming convention
  - Regular files are copied via C(ansible.builtin.copy) with content
  - Files with C(.secrets) in the path are copied with vault decryption (C(.secrets) stripped from dest name)
  - Files ending in C(.j2) are rendered as Jinja2 templates (C(.j2) stripped from dest name)
  - Supports C(state=absent) to remove previously copied files from the destination
version_added: "1.0.0"
options:
  src:
    description:
      - Source directory to scan for files on the controller
      - Resolved relative to the playbook file directory if not absolute
    required: true
    type: str
  dest:
    description:
      - Destination directory on the target host
      - Directory structure from source is preserved
    required: true
    type: str
  state:
    description:
      - C(present) copies files from source to destination
      - C(absent) removes files from destination that match the source tree structure
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - cenk1cenk2
notes:
  - This is an action plugin that scans files on the controller
  - File categorization is checked in order — C(.j2) first, then C(.secrets), then regular
  - C(.secrets) and C(.j2) suffixes are stripped from destination filenames
  - With C(state=absent), the source is still scanned to determine which files to remove
"""

EXAMPLES = r"""
- name: Copy configuration files
  cenk1cenk2.reloaded.copy_files:
    src: ./files/conf
    dest: /etc/myapp

- name: Copy systemd units
  cenk1cenk2.reloaded.copy_files:
    src: ./files/systemd/
    dest: /etc/systemd/system

- name: Remove previously copied files
  cenk1cenk2.reloaded.copy_files:
    src: ./files/conf
    dest: /etc/myapp
    state: absent
"""

RETURN = r"""
changed:
  description: Whether any files were created, modified, or removed
  returned: always
  type: bool
src:
  description: Resolved source directory path
  returned: always
  type: str
dest:
  description: Destination directory path
  returned: always
  type: str
copied_files:
  description: List of regular files copied (relative paths)
  returned: when state is 'present'
  type: list
  elements: str
copied_secrets:
  description: List of vault-encrypted files copied (relative paths)
  returned: when state is 'present'
  type: list
  elements: str
copied_templates:
  description: List of templates rendered (relative paths)
  returned: when state is 'present'
  type: list
  elements: str
removed_files:
  description: List of files removed from destination (absolute paths)
  returned: when state is 'absent'
  type: list
  elements: str
diff:
  description: File diffs from copy/template actions
  returned: when diff mode is enabled and files changed
  type: list
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
