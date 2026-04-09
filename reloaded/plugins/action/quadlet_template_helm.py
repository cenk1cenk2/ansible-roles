#!/usr/bin/env python3

from __future__ import annotations

__metaclass__ = type

import os

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
    _VALID_ARGS = frozenset(
        (
            "chart",
            "dest",
            "name",
            "values_files",
            "values",
            "set_values",
            "namespace",
            "include_crds",
            "binary_path",
        )
    )

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                chart=dict(type="str", required=True),
                dest=dict(type="str", required=True),
                name=dict(type="str", required=True),
                values_files=dict(type="list", elements="str", default=[]),
                values=dict(type="dict", default={}),
                set_values=dict(type="list", elements="dict", default=[]),
                namespace=dict(type="str"),
                include_crds=dict(type="bool", default=False),
                binary_path=dict(type="path"),
            ),
        )

        result = super().run(tmp, task_vars)
        result.update(changed=False)

        chart = self._resolve_path(args["chart"])
        name = args["name"]

        display.v(f"Rendering chart '{chart}' as release '{name}'")

        values_files = [
            self._resolve_path(f) for f in args["values_files"]
        ]
        if values_files:
            display.v(f"Values files: {', '.join(values_files)}")

        if args["values"]:
            display.v(f"Inline values keys: {', '.join(args['values'].keys())}")

        helm_args = dict(
            chart_ref=chart,
            release_name=name,
            values_files=values_files,
            release_values=args["values"],
            include_crds=args["include_crds"],
        )

        if args["set_values"]:
            helm_args["set_values"] = args["set_values"]
            display.v(f"Set values: {len(args['set_values'])} entries")

        if args.get("namespace"):
            helm_args["release_namespace"] = args["namespace"]

        if args.get("binary_path"):
            helm_args["binary_path"] = args["binary_path"]

        # Run helm on the controller, not the target
        # helm binary and chart files are local, only the rendered output goes remote
        original_connection = self._connection
        try:
            self._connection = LocalConnection(self._play_context)
            helm_result = self._execute_module(
                module_name="kubernetes.core.helm_template",
                module_args=helm_args,
                task_vars=task_vars,
            )
        finally:
            self._connection = original_connection

        if helm_result.get("failed"):
            stderr = helm_result.get("stderr", "")
            msg = helm_result.get("msg", stderr or "helm template failed")
            display.warning(f"helm template failed for '{name}': {msg}")
            result["failed"] = True
            result["msg"] = msg
            result["command"] = helm_result.get("command", "")

            return result

        manifest = helm_result.get("stdout", "")
        command = helm_result.get("command", "")
        dest_path = os.path.join(args["dest"], f"{name}.yaml")

        display.v(f"Helm command: {command}")
        display.v(f"Rendered {len(manifest)} bytes, deploying to {dest_path}")

        deploy_result = self._deploy(manifest, dest_path, task_vars)

        filename = f"{name}.yaml"
        changed = deploy_result.get("changed", False)
        result.update(
            changed=changed,
            dest=dest_path,
            filename=filename,
            manifest=manifest,
            command=command,
            msg=f"Rendered chart '{name}' to {dest_path}",
        )

        if "diff" in deploy_result:
            result["diff"] = deploy_result["diff"]

        if deploy_result.get("failed"):
            display.warning(f"Failed to deploy manifest to {dest_path}")
            result["failed"] = True
            result["msg"] = (
                f"Failed to write manifest: {deploy_result.get('msg', 'Unknown error')}"
            )
        else:
            display.v(f"Deploy complete, changed={changed}")

        return result

    def _resolve_path(self, path):
        if os.path.isabs(path):
            return path

        return os.path.normpath(os.path.join(self._loader.get_basedir(), path))

    def _deploy(self, content, dest_path, task_vars):
        new_task = self._task.copy()
        new_task.args = {"content": content, "dest": dest_path, "mode": "0644"}

        copy_action = self._shared_loader_obj.action_loader.get(
            "ansible.builtin.copy",
            task=new_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj,
        )

        return copy_action.run(task_vars=task_vars)
