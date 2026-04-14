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
  - Copies files from the clone to the target using C(copy_files) internally
  - Supports all C(copy_files) features (templates, secrets, directory structure)
  - Temporary clone is always cleaned up after completion
  - Supports C(state=absent) to remove the destination directory
version_added: "1.0.0"
options:
  git:
    description:
      - Arguments passed directly to C(ansible.builtin.git) module
      - C(repo) is required within this dict
      - Defaults applied if not specified — C(clone=true), C(update=true), C(single_branch=true), C(version=main)
      - All other C(ansible.builtin.git) parameters are supported (e.g., C(force), C(depth), C(key_file))
    required: true
    type: dict
    suboptions:
      repo:
        description: Git repository URL or path
        required: true
        type: str
      version:
        description: Branch, tag, or commit to check out
        type: str
        default: main
      clone:
        description: Whether to clone the repository if it does not exist
        type: bool
        default: true
      update:
        description: Whether to update the repository if it already exists
        type: bool
        default: true
      single_branch:
        description: Clone only the history leading to the tip of the specified branch
        type: bool
        default: true
      depth:
        description: Create a shallow clone with truncated history
        type: int
      force:
        description: Discard any modified tracked files
        type: bool
        default: false
      key_file:
        description: Path to a private key for SSH authentication
        type: path
  dest:
    description:
      - Destination directory on the target host
      - With C(state=absent), this directory is removed entirely
    required: true
    type: str
  src:
    description:
      - Subdirectory within the cloned repo to copy from
      - If omitted, copies from the repo root
      - Example — C(src=src) copies only the C(src/) subfolder of the cloned repo
    required: false
    type: str
  copy:
    description:
      - Additional options passed to C(copy_files) plugin
    required: false
    type: dict
    default: {}
    suboptions:
      state:
        description: C(present) or C(absent) passed to copy_files
        type: str
        choices: ['present', 'absent']
        default: present
  state:
    description:
      - C(present) clones the repo and copies files to the destination
      - C(absent) removes the destination directory
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - cenk1cenk2
notes:
  - Git clone runs on the controller via LocalConnection, file copy runs to the target
  - Temporary clone directory is always cleaned up, even on failure
  - The C(git.dest) parameter is managed internally — do not set it
"""

EXAMPLES = r"""
- name: Deploy zsh config from a git repo subfolder
  cenk1cenk2.reloaded.degit:
    git:
      repo: git@gitlab.kilic.dev:config/config-zsh.git
      version: main
    src: src
    dest: '{{ ansible_facts["env"]["HOME"] }}/.config/znap/'

- name: Deploy full repo contents
  cenk1cenk2.reloaded.degit:
    git:
      repo: https://github.com/cenk1cenk2/nvim.git
      version: rolling
    dest: '{{ ansible_facts["env"]["HOME"] }}/.config/nvim/'

- name: Override git defaults
  cenk1cenk2.reloaded.degit:
    git:
      repo: git@gitlab.kilic.dev:config/dotfiles.git
      version: develop
      single_branch: false
      force: true
    dest: /etc/myapp/

- name: Remove deployed files
  cenk1cenk2.reloaded.degit:
    git:
      repo: git@gitlab.kilic.dev:config/config-zsh.git
    dest: '{{ ansible_facts["env"]["HOME"] }}/.config/znap/'
    state: absent
"""

RETURN = r"""
changed:
  description: Whether any files were created, modified, or removed
  returned: always
  type: bool
dest:
  description: Destination directory path
  returned: always
  type: str
src:
  description: Resolved source path within the clone (includes subpath if specified)
  returned: when state is 'present'
  type: str
repo:
  description: Git repository URL that was cloned
  returned: when state is 'present'
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
diff:
  description: File diffs from copy operations
  returned: when diff mode is enabled and files changed
  type: list
msg:
  description: Human-readable result message
  returned: always
  type: str
"""
