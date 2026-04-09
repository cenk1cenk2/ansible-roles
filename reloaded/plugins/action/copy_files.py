#!/usr/bin/env python3

from __future__ import annotations

__metaclass__ = type

import os

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

DOCUMENTATION = """
---
"""

EXAMPLES = """
"""

RETURN = """
"""


class ActionModule(ActionBase):
    _VALID_ARGS = frozenset(("src", "dest", "state"))

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                src=dict(type="str", required=True),
                dest=dict(type="str", required=True),
                state=dict(type="str", default="present", choices=["present", "absent"]),
            ),
        )

        result = super().run(tmp, task_vars)
        result.update(changed=False, copied_files=[], copied_secrets=[], copied_templates=[])

        src = self._resolve_path(args["src"])
        dest = args["dest"]

        if args["state"] == "absent":
            return self._remove(result, src, dest, task_vars)

        if not os.path.isdir(src):
            return self._fail(result, f"Source directory '{src}' does not exist")

        display.v(f"Scanning files in '{src}'")

        directories, files, secrets, templates = self._scan(src)

        display.v(
            f"Found {len(files)} file(s), {len(secrets)} secret(s), "
            f"{len(templates)} template(s), {len(directories)} director(ies)"
        )

        # Ensure dest and subdirectories exist
        dirs_to_create = [dest] + [os.path.join(dest, d) for d in directories]
        for d in dirs_to_create:
            dir_result = self._execute_module(
                module_name="ansible.builtin.file",
                module_args={"path": d, "state": "directory"},
                task_vars=task_vars,
            )
            if dir_result.get("failed"):
                return self._fail(result, f"Failed to create directory '{d}': {dir_result.get('msg')}")

        changed = False
        diffs = []

        # Copy regular files via synchronize
        for rel_path, abs_path in files:
            dest_path = os.path.join(dest, rel_path)
            display.vv(f"Syncing file: {rel_path} -> {dest_path}")
            r = self._run_action(
                "ansible.posix.synchronize",
                {"src": abs_path, "dest": dest_path},
                task_vars,
            )
            if r.get("failed"):
                return self._fail(result, f"Failed to copy '{rel_path}': {r.get('msg')}")
            if r.get("changed"):
                changed = True
            if "diff" in r:
                diffs.append(r["diff"])
            result["copied_files"].append(rel_path)

        # Copy secrets with vault decryption
        for rel_path, abs_path in secrets:
            dest_name = rel_path.replace(".secrets", "")
            dest_path = os.path.join(dest, dest_name)
            display.vv(f"Decrypting secret: {rel_path} -> {dest_path}")
            r = self._run_action(
                "ansible.builtin.copy",
                {"src": abs_path, "dest": dest_path, "decrypt": True},
                task_vars,
            )
            if r.get("failed"):
                return self._fail(result, f"Failed to copy secret '{rel_path}': {r.get('msg')}")
            if r.get("changed"):
                changed = True
            if "diff" in r:
                diffs.append(r["diff"])
            result["copied_secrets"].append(rel_path)

        # Render templates
        for rel_path, abs_path in templates:
            dest_name = rel_path.replace(".secrets", "").removesuffix(".j2")
            dest_path = os.path.join(dest, dest_name)
            display.vv(f"Rendering template: {rel_path} -> {dest_path}")
            r = self._run_action(
                "ansible.builtin.template",
                {"src": abs_path, "dest": dest_path},
                task_vars,
            )
            if r.get("failed"):
                return self._fail(result, f"Failed to render template '{rel_path}': {r.get('msg')}")
            if r.get("changed"):
                changed = True
            if "diff" in r:
                diffs.append(r["diff"])
            result["copied_templates"].append(rel_path)

        if diffs:
            result["diff"] = diffs

        total = len(files) + len(secrets) + len(templates)
        result["changed"] = changed
        result["src"] = src
        result["dest"] = dest
        result["msg"] = f"Processed {total} file(s) from '{src}' to '{dest}'"

        display.v(f"Copy complete, changed={changed}")

        return result

    def _remove(self, result, src, dest, task_vars):
        if not os.path.isdir(src):
            return self._fail(result, f"Source directory '{src}' does not exist")

        display.v(f"Removing files from '{dest}' matching '{src}'")

        _, files, secrets, templates = self._scan(src)

        removed = []
        changed = False

        all_targets = []
        for rel_path, _ in files:
            all_targets.append(os.path.join(dest, rel_path))
        for rel_path, _ in secrets:
            all_targets.append(os.path.join(dest, rel_path.replace(".secrets", "")))
        for rel_path, _ in templates:
            all_targets.append(os.path.join(dest, rel_path.replace(".secrets", "").removesuffix(".j2")))

        for target in all_targets:
            r = self._execute_module(
                module_name="ansible.builtin.file",
                module_args={"path": target, "state": "absent"},
                task_vars=task_vars,
            )
            if r.get("failed"):
                return self._fail(result, f"Failed to remove '{target}': {r.get('msg')}")
            if r.get("changed"):
                changed = True
                removed.append(target)

        result["changed"] = changed
        result["src"] = src
        result["dest"] = dest
        result["removed_files"] = removed
        result["msg"] = f"Removed {len(removed)} file(s) from '{dest}'"

        display.v(f"Remove complete, {len(removed)} file(s) removed")

        return result

    def _fail(self, result, msg):
        result["failed"] = True
        result["msg"] = msg

        return result

    def _resolve_path(self, path):
        if os.path.isabs(path):
            return path

        return os.path.normpath(os.path.join(self._loader.get_basedir(), path))

    def _scan(self, src):
        directories = []
        files = []
        secrets = []
        templates = []

        for root, dirs, filenames in os.walk(src):
            rel_root = os.path.relpath(root, src)

            for d in sorted(dirs):
                rel_dir = os.path.join(rel_root, d) if rel_root != "." else d
                directories.append(rel_dir)

            for f in sorted(filenames):
                rel_path = os.path.join(rel_root, f) if rel_root != "." else f
                abs_path = os.path.join(root, f)

                if f.endswith(".j2"):
                    templates.append((rel_path, abs_path))
                elif ".secrets" in rel_path:
                    secrets.append((rel_path, abs_path))
                else:
                    files.append((rel_path, abs_path))

        return directories, files, secrets, templates

    def _run_action(self, action_name, action_args, task_vars):
        new_task = self._task.copy()
        new_task.args = action_args

        action = self._shared_loader_obj.action_loader.get(
            action_name,
            task=new_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj,
        )

        return action.run(task_vars=task_vars)
