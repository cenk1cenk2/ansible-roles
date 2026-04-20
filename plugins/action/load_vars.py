#!/usr/bin/env python3

from __future__ import annotations

__metaclass__ = type

import glob
import os

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

try:
    from ansible.plugins.action import VariableLayer
    from ansible._internal._task import TaskContext

    _HAS_VARIABLE_LAYER = True
except ImportError:
    _HAS_VARIABLE_LAYER = False

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
        ("mode", "root", "pattern", "environment", "common", "strict", "hash_behaviour", "scope")
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
                hash_behaviour=dict(
                    type="str",
                    choices=["replace", "merge"],
                    default=C.DEFAULT_HASH_BEHAVIOUR,
                ),
                scope=dict(
                    type="str",
                    choices=["global", "return"],
                    default="global",
                ),
            ),
            required_if=[
                ("mode", "pattern", ("pattern",)),
                ("mode", "environment", ("environment",)),
            ],
        )

        self._merge = args["hash_behaviour"] == "merge"
        self._scope_return = args["scope"] == "return"

        result = super().run(tmp, task_vars)
        result.update(changed=False, loaded_files=[], variables_loaded=0)

        args["root"] = self._resolve_path(args["root"])
        root = args["root"]
        if not os.path.isdir(root):
            return self._fail(result, f"Root directory '{root}' does not exist")

        display.v(f"Loading variables: mode={args['mode']}, root={root}")

        if args["mode"] == "pattern":
            return self._run_pattern(result, args, task_vars)

        return self._run_environment(result, args, task_vars)

    def _fail(self, result, msg):
        result["failed"] = True
        result["msg"] = msg

        return result

    def _register_variables(self, result, facts):
        if _HAS_VARIABLE_LAYER:
            self.register_host_variables(facts, VariableLayer.INCLUDE_VARS)
            self.register_host_variables({}, VariableLayer.CACHEABLE_FACT)
        else:
            result["ansible_facts"] = facts

    def _resolve_path(self, path):
        if os.path.isabs(path):
            return path

        return os.path.normpath(os.path.join(self._loader.get_basedir(), path))

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
        if self._scope_return:
            return self._load_vars_files_local(files)

        return self._load_vars_files_include(files, task_vars)

    def _load_vars_files_include(self, files, task_vars):
        facts = {}
        loaded = []
        per_file = []

        for vars_file in files:
            new_task = self._task.copy()
            new_task.args = {
                "file": vars_file,
            }

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

            if _HAS_VARIABLE_LAYER:
                TaskContext.current().pending_changes.register_host_variables.pop(
                    VariableLayer.INCLUDE_VARS, None
                )

            if r.get("failed"):
                return None, f"Failed to load '{vars_file}': {r.get('msg', 'Unknown error')}"

            if "ansible_facts" in r:
                file_data = r["ansible_facts"]
                facts = combine_vars(facts, file_data, merge=self._merge)
                task_vars = combine_vars(task_vars, file_data, merge=self._merge)
                loaded.append(vars_file)
                per_file.append({
                    "filename": os.path.basename(vars_file),
                    "path": vars_file,
                    "data": file_data,
                })

        return (facts, loaded, per_file), None

    def _load_vars_files_local(self, files):
        facts = {}
        loaded = []
        per_file = []

        for vars_file in files:
            try:
                file_data = self._loader.load_from_file(vars_file)
            except Exception as e:
                return None, f"Failed to load '{vars_file}': {e}"

            if file_data is None:
                file_data = {}

            if not isinstance(file_data, dict):
                return None, f"File '{vars_file}' does not contain a YAML dictionary"

            # Template the data to resolve Jinja2 expressions
            file_data = self._templar.template(file_data)

            facts = combine_vars(facts, file_data, merge=self._merge)
            loaded.append(vars_file)
            per_file.append({
                "filename": os.path.basename(vars_file),
                "path": vars_file,
                "data": file_data,
            })

        return (facts, loaded, per_file), None

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

        facts, loaded, per_file = data

        if self._scope_return:
            result["vars"] = facts
        else:
            self._register_variables(result, facts)

        result["root"] = root
        result["matched_files"] = matched
        result["loaded_files"] = sorted(loaded)
        result["files"] = per_file
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
        facts, loaded, per_file = data

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
        env_facts, env_loaded, env_per_file = env_data
        facts = combine_vars(facts, env_facts, merge=self._merge)
        loaded.extend(env_loaded)
        per_file.extend(env_per_file)

        if self._scope_return:
            result["vars"] = facts
        else:
            self._register_variables(result, facts)

        result["root"] = root
        result["loaded_files"] = sorted(loaded)
        result["files"] = per_file
        result["variables_loaded"] = len(facts)
        result["msg"] = f"Loaded {len(loaded)} file(s) in environment mode"

        display.v(
            f"Environment mode: loaded {len(loaded)} file(s) "
            f"({len(common_files)} common + {len(env_files)} environment)"
        )

        return result
