#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: degit
short_description: Clone a git repo and copy its files to a destination
description:
  - Clones a git repository to a temporary directory on the controller
  - Copies files from the clone to the target using copy_files
  - Supports all copy_files features (templates, secrets, directory structure)
  - Cleans up the temporary clone after completion
version_added: "1.0.0"
options:
  git:
    description:
      - Git module arguments passed directly to ansible.builtin.git
      - C(repo) is required, other options default to clone=true, update=true, single_branch=true, version=main
    required: true
    type: dict
  dest:
    description:
      - Destination directory on the target host
    required: true
    type: str
  src:
    description:
      - Subdirectory within the cloned repo to copy from
      - If omitted, copies from the repo root
      - Example C(src) to copy only the C(src/) subfolder of the repo
    required: false
    type: str
  copy:
    description:
      - Additional options passed to copy_files
    required: false
    type: dict
    default: {}
  state:
    description:
      - C(present) clones and copies, C(absent) removes the dest directory
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - cenk1cenk2
notes:
  - Git clone runs on the controller, file copy runs to the target
  - Temporary clone directory is always cleaned up
"""

EXAMPLES = r"""
- name: Deploy zsh config from git
  cenk1cenk2.reloaded.degit:
    git:
      repo: git@gitlab.kilic.dev:config/config-zsh.git
      version: main
    src: src
    dest: '{{ ansible_facts["env"]["HOME"] }}/.config/znap/'

- name: Deploy full repo
  cenk1cenk2.reloaded.degit:
    git:
      repo: git@gitlab.kilic.dev:config/dotfiles.git
    dest: /etc/myapp/
"""

RETURN = r"""
changed:
  description: Whether any files were created or modified
  returned: always
  type: bool
dest:
  description: Destination directory
  returned: always
  type: str
repo:
  description: Git repository URL
  returned: success
  type: str
copied_files:
  description: List of regular files copied
  returned: success
  type: list
copied_secrets:
  description: List of vault-encrypted files copied
  returned: success
  type: list
copied_templates:
  description: List of templates rendered
  returned: success
  type: list
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
