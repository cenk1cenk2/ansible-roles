#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: copy_files
short_description: Copy files from a source directory tree to a destination
description:
  - Scans a source directory and copies files to a destination preserving structure
  - Automatically handles three file types based on naming conventions
  - Regular files are synced via synchronize (rsync)
  - Files with C(.secrets) in the path are copied with vault decryption
  - Files ending in C(.j2) are rendered as Jinja2 templates
  - The C(.secrets) and C(.j2) suffixes are stripped from destination filenames
version_added: "1.0.0"
options:
  src:
    description:
      - Source directory to scan for files
      - Resolved relative to the playbook directory if not absolute
    required: true
    type: str
  dest:
    description:
      - Destination directory on the target host
      - Directory structure from source is preserved
    required: true
    type: str
author:
  - cenk1cenk2
notes:
  - This is an action plugin that scans files on the controller
  - Requires ansible.posix collection for synchronize
  - File categorization rules are mutually exclusive and checked in order - .j2 first, then .secrets, then regular
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
"""

RETURN = r"""
changed:
  description: Whether any files were created or modified
  returned: always
  type: bool
copied_files:
  description: List of regular files copied
  returned: always
  type: list
  elements: str
copied_secrets:
  description: List of vault-encrypted files copied
  returned: always
  type: list
  elements: str
copied_templates:
  description: List of templates rendered
  returned: always
  type: list
  elements: str
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
