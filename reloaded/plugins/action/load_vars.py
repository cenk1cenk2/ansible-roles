#!/usr/bin/env python3

from __future__ import annotations

__metaclass__ = type

import glob
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
    _VALID_ARGS = frozenset(
        ("mode", "root", "pattern", "environment", "common", "strict")
    )

    SUPPORTED_EXTENSIONS = ("*.yml", "*.yaml", "*.json")

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                mode=dict(
                    type="str", required=True, choices=["pattern", "environment"]
                ),
                root=dict(type="str", required=True),
                pattern=dict(type="str"),
                environment=dict(type="str"),
                common=dict(type="str", default="base"),
                strict=dict(type="bool", default=False),
            ),
            required_if=[
                ("mode", "pattern", ("pattern",)),
                ("mode", "environment", ("environment",)),
            ],
        )

        result = super().run(tmp, task_vars)
        result.update(changed=False, loaded_files=[], variables_loaded=0)

        root = args["root"]
        if not os.path.isdir(root):
            return self._fail(result, f"Root directory '{root}' does not exist")

        if args["mode"] == "pattern":
            return self._run_pattern(result, args, task_vars)

        return self._run_environment(result, args, task_vars)

    def _fail(self, result, msg):
        result["failed"] = True
        result["msg"] = msg

        return result

    def _glob_vars_files(self, directory, pattern=None):
        if pattern:
            base = (
                os.path.join(directory, pattern)
                if not os.path.isabs(pattern)
                else pattern
            )
            if base.endswith((".yml", ".yaml", ".json")):
                patterns = [base]
            else:
                patterns = [base + ext for ext in (".yml", ".yaml", ".json")]
        else:
            patterns = [os.path.join(directory, ext) for ext in self.SUPPORTED_EXTENSIONS]

        files = []
        for p in patterns:
            files.extend(glob.glob(p, recursive=True))

        return sorted(set(files))

    def _load_vars_files(self, files, result, task_vars):
        facts = {}
        loaded = []

        for vars_file in files:
            new_task = self._task.copy()
            new_task.args = {"file": vars_file}

            action = self._shared_loader_obj.action_loader.get(
                "ansible.builtin.include_vars",
                task=new_task,
                connection=self._connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=self._templar,
                shared_loader_obj=self._shared_loader_obj,
            )
            r = action.run(task_vars=task_vars)

            if r.get("failed"):
                return None, f"Failed to load '{vars_file}': {r.get('msg', 'Unknown error')}"

            if "ansible_facts" in r:
                facts.update(r["ansible_facts"])
                task_vars.update(r["ansible_facts"])
                loaded.append(vars_file)

        return (facts, loaded), None

    def _run_pattern(self, result, args, task_vars):
        root = args["root"]
        pattern = args["pattern"]
        strict = args["strict"]

        matched = self._glob_vars_files(root, pattern)

        if not matched:
            if strict:
                return self._fail(
                    result,
                    f"No files matched pattern '{pattern}' in '{root}' (strict mode)",
                )
            display.warning(f"No files matched pattern '{pattern}' in '{root}'")

        data, err = self._load_vars_files(matched, result, task_vars)
        if err:
            return self._fail(result, err)

        facts, loaded = data
        result["ansible_facts"] = facts
        result["matched_files"] = matched
        result["loaded_files"] = sorted(loaded)
        result["variables_loaded"] = len(facts)
        result["msg"] = f"Loaded {len(loaded)} file(s) matching '{pattern}'"

        display.v(
            f"Pattern mode: loaded {len(loaded)} file(s), {len(facts)} variable(s)"
        )

        return result

    def _run_environment(self, result, args, task_vars):
        root = args["root"]
        environment = args["environment"]
        common = args["common"]
        strict = args["strict"]

        common_files = self._glob_vars_files(os.path.join(root, common))
        data, err = self._load_vars_files(common_files, result, task_vars)
        if err:
            return self._fail(result, err)
        facts, loaded = data

        env_files = self._glob_vars_files(os.path.join(root, environment))

        if strict and not env_files:
            return self._fail(
                result,
                f"No files in environment directory '{root}/{environment}' (strict mode)",
            )

        if not common_files and not env_files:
            display.warning(
                f"No files in '{common}' or '{environment}' directories"
            )

        env_data, err = self._load_vars_files(env_files, result, task_vars)
        if err:
            return self._fail(result, err)
        env_facts, env_loaded = env_data
        facts.update(env_facts)
        loaded.extend(env_loaded)

        result["ansible_facts"] = facts
        result["loaded_files"] = sorted(loaded)
        result["variables_loaded"] = len(facts)
        result["msg"] = f"Loaded {len(loaded)} file(s) in environment mode"

        display.v(
            f"Environment mode: loaded {len(loaded)} file(s) "
            f"({len(common_files)} common + {len(env_files)} environment)"
        )

        return result
