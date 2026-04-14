#!/usr/bin/env python3

from __future__ import annotations

__metaclass__ = type

import os
import tempfile

from ansible.plugins.action import ActionBase
from ansible.plugins.connection.local import Connection as LocalConnection
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
    _VALID_ARGS = frozenset(("git", "copy", "dest", "src", "state"))

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                git=dict(type="dict", required=True),
                dest=dict(type="str", required=True),
                src=dict(type="str"),
                copy=dict(type="dict", default={}),
                state=dict(type="str", default="present", choices=["present", "absent"]),
            ),
        )

        result = super().run(tmp, task_vars)
        result.update(changed=False)

        if args["state"] == "absent":
            return self._absent(result, args, task_vars)

        return self._present(result, args, task_vars)

    def _present(self, result, args, task_vars):
        git_args = args["git"]

        if "repo" not in git_args:
            return self._fail(result, "'git.repo' is required")

        git_args.setdefault("clone", True)
        git_args.setdefault("update", True)
        git_args.setdefault("single_branch", True)
        git_args.setdefault("version", "main")

        tmpdir = tempfile.mkdtemp(prefix="degit_")
        git_args["dest"] = tmpdir

        display.v(f"Cloning {git_args['repo']} to {tmpdir}")

        try:
            # Clone on the controller
            original_connection = self._connection
            try:
                self._connection = LocalConnection(self._play_context)
                git_result = self._execute_module(
                    module_name="ansible.builtin.git",
                    module_args=git_args,
                    task_vars=task_vars,
                )
            finally:
                self._connection = original_connection

            if git_result.get("failed"):
                return self._fail(
                    result,
                    f"Git clone failed: {git_result.get('msg', '')}",
                )

            # Determine src within the clone
            src_subpath = args.get("src")
            if src_subpath:
                copy_src = os.path.join(tmpdir, src_subpath)
            else:
                copy_src = tmpdir

            if not os.path.isdir(copy_src):
                return self._fail(
                    result,
                    f"Source path '{copy_src}' does not exist in cloned repo",
                )

            dest = args["dest"]

            display.v(f"Copying files from {copy_src} to {dest}")

            # Delegate to copy_files
            copy_args = dict(args.get("copy", {}))
            copy_args["src"] = copy_src
            copy_args["dest"] = dest
            copy_args.setdefault("state", "present")

            new_task = self._task.copy()
            new_task.args = copy_args

            copy_action = self._shared_loader_obj.action_loader.get(
                "cenk1cenk2.reloaded.copy_files",
                task=new_task,
                connection=self._connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=self._templar,
                shared_loader_obj=self._shared_loader_obj,
            )
            copy_result = copy_action.run(task_vars=task_vars)

            result.update(
                changed=copy_result.get("changed", False),
                dest=dest,
                src=copy_src,
                repo=git_args["repo"],
                copied_files=copy_result.get("copied_files", []),
                copied_secrets=copy_result.get("copied_secrets", []),
                copied_templates=copy_result.get("copied_templates", []),
                msg=f"Cloned {git_args['repo']} and copied to {dest}",
            )

            if copy_result.get("failed"):
                result["failed"] = True
                result["msg"] = copy_result.get("msg", "copy_files failed")

            if "diff" in copy_result:
                result["diff"] = copy_result["diff"]

        finally:
            # Clean up temp dir
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)

        return result

    def _absent(self, result, args, task_vars):
        dest = args["dest"]
        display.v(f"Removing {dest}")

        file_result = self._execute_module(
            module_name="ansible.builtin.file",
            module_args={"path": dest, "state": "absent"},
            task_vars=task_vars,
        )

        result.update(
            changed=file_result.get("changed", False),
            dest=dest,
            msg=f"Removed '{dest}'" if file_result.get("changed") else f"'{dest}' already absent",
        )

        if file_result.get("failed"):
            result["failed"] = True
            result["msg"] = f"Failed to remove '{dest}': {file_result.get('msg', '')}"

        return result

    def _fail(self, result, msg):
        result["failed"] = True
        result["msg"] = msg

        return result
