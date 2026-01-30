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
        (
            "mode",
            "root",
            "pattern",
            "environment",
            "common",
            "strict",
            "verbosity",
        )
    )

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                mode=dict(type="str"),
                root=dict(type="str"),
                pattern=dict(type="str"),
                environment=dict(type="str"),
                common=dict(type="bool"),
                strict=dict(type="bool"),
                verbosity=dict(type="int", default=0),
            ),
        )

        result = super(ActionModule, self).run(tmp, task_vars)

        result.update(dict(changed=False, failed=False, msg="", skipped=False))

        # Validate mode parameter
        mode = args.get("mode")
        valid_modes = ["pattern", "environment"]

        if mode and mode not in valid_modes:
            result["failed"] = True
            result["msg"] = f"Invalid mode '{mode}'. Mode must be one of: {', '.join(valid_modes)}"
            return result

        # Validate root directory exists
        root = args.get("root")
        if root and not os.path.exists(root):
            result["failed"] = True
            result["msg"] = f"Root directory '{root}' does not exist"
            return result

        # Validate mode-specific required parameters
        if mode == "pattern":
            pattern = args.get("pattern")
            if not pattern:
                result["failed"] = True
                result["msg"] = "Pattern mode requires 'pattern' parameter"
                return result

        if mode == "environment":
            environment = args.get("environment")
            if not environment:
                result["failed"] = True
                result["msg"] = "Environment mode requires 'environment' parameter"
                return result

        # Pattern mode implementation
        if mode == "pattern":
            pattern = args.get("pattern")

            # Build file patterns for all supported extensions
            # Support glob patterns like "*.yml" or "subdir/**/*.yml"
            base_pattern = os.path.join(root, pattern) if not os.path.isabs(pattern) else pattern

            # If pattern already has extension, use it directly
            # Otherwise, try all supported extensions
            if base_pattern.endswith(('.yml', '.yaml', '.json')):
                patterns_to_search = [base_pattern]
            else:
                # Remove any extension from pattern and add all supported extensions
                base_without_ext = base_pattern.rstrip('*')
                patterns_to_search = [
                    base_without_ext + '.yml',
                    base_without_ext + '.yaml',
                    base_without_ext + '.json',
                ]

            # Glob all matching files
            matched_files = []
            for pattern_str in patterns_to_search:
                matched_files.extend(glob.glob(pattern_str, recursive=True))

            # Sort for deterministic order
            matched_files = sorted(set(matched_files))

            # Handle strict mode
            strict = args.get("strict", False)
            if strict and len(matched_files) == 0:
                result["failed"] = True
                result["msg"] = f"In strict mode, at least one file must match pattern '{pattern}' in directory '{root}'"
                return result

            # Load variables from each matched file using include_vars
            loaded_files = []
            ansible_facts = {}
            verbosity = args.get("verbosity", 0)

            for vars_file in matched_files:
                if verbosity >= 1:
                    display.v(f"Loading variables from: {vars_file}")

                # Execute include_vars action plugin for this file
                include_vars_result = self._execute_module(
                    module_name="ansible.builtin.include_vars",
                    module_args=dict(file=vars_file),
                    task_vars=task_vars,
                    tmp=tmp,
                )

                # Check if include_vars succeeded
                if include_vars_result.get("failed", False):
                    result["failed"] = True
                    result["msg"] = f"Failed to load variables from '{vars_file}': {include_vars_result.get('msg', 'Unknown error')}"
                    return result

                # Collect the loaded variables (they are in ansible_facts)
                if "ansible_facts" in include_vars_result:
                    ansible_facts.update(include_vars_result["ansible_facts"])
                    loaded_files.append(vars_file)

            # Update result with loaded variables
            result["ansible_facts"] = ansible_facts
            result["matched_files"] = matched_files
            result["loaded_files"] = loaded_files
            result["msg"] = f"Loaded variables from {len(loaded_files)} file(s) matching pattern '{pattern}'"

        return result
