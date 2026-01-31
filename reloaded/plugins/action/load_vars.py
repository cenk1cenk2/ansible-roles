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
                common=dict(type="str", default="base"),
                strict=dict(type="bool"),
                verbosity=dict(type="int", default=0),
            ),
        )

        result = super(ActionModule, self).run(tmp, task_vars)

        result.update(
            dict(
                changed=False,
                failed=False,
                msg="",
                skipped=False,
                loaded_files=[],
                variables_loaded=0,
            )
        )

        # Validate mode parameter (required)
        mode = args.get("mode")
        if not mode:
            result["failed"] = True
            result["msg"] = "Required parameter 'mode' is missing"
            return result

        valid_modes = ["pattern", "environment"]
        if mode not in valid_modes:
            result["failed"] = True
            result["msg"] = f"Invalid mode '{mode}'. Mode must be one of: {', '.join(valid_modes)}"
            return result

        # Validate root parameter (required)
        root = args.get("root")
        if not root:
            result["failed"] = True
            result["msg"] = "Required parameter 'root' is missing"
            return result

        # Validate root directory exists
        if not os.path.exists(root):
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
            verbosity = args.get("verbosity", 0)

            display.vv(f"Pattern mode: searching for pattern '{pattern}' in root '{root}'")

            # Build file patterns for all supported extensions
            # Support glob patterns like "*.yml" or "subdir/**/*.yml"
            base_pattern = os.path.join(root, pattern) if not os.path.isabs(pattern) else pattern

            # If pattern already has extension, use it directly
            # Otherwise, try all supported extensions
            if base_pattern.endswith(('.yml', '.yaml', '.json')):
                patterns_to_search = [base_pattern]
                display.vvv(f"Pattern has extension, using: {base_pattern}")
            else:
                # Remove any extension from pattern and add all supported extensions
                base_without_ext = base_pattern.rstrip('*')
                patterns_to_search = [
                    base_without_ext + '.yml',
                    base_without_ext + '.yaml',
                    base_without_ext + '.json',
                ]
                display.vvv(f"Pattern has no extension, searching: {', '.join(patterns_to_search)}")

            # Glob all matching files
            matched_files = []
            for pattern_str in patterns_to_search:
                found = glob.glob(pattern_str, recursive=True)
                if found:
                    display.vvv(f"Pattern '{pattern_str}' matched {len(found)} file(s)")
                matched_files.extend(found)

            # Sort for deterministic order
            matched_files = sorted(set(matched_files))

            if matched_files:
                display.vv(f"Found {len(matched_files)} matching file(s): {', '.join(matched_files)}")

            # Handle strict mode
            strict = args.get("strict", False)
            if strict and len(matched_files) == 0:
                result["failed"] = True
                result["msg"] = f"In strict mode, variables files should be matched in the given directory: {root}"
                return result

            # Warn if no files matched in non-strict mode
            if not strict and len(matched_files) == 0:
                display.warning(f"No files matched pattern '{pattern}' in directory '{root}'")
                display.vv("No files to load in pattern mode")

            # Load variables from each matched file using include_vars
            loaded_files = []
            ansible_facts = {}

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
            result["loaded_files"] = sorted(loaded_files)
            result["variables_loaded"] = len(ansible_facts)
            result["msg"] = f"Loaded variables from {len(loaded_files)} file(s) matching pattern '{pattern}'"

            display.v(f"Pattern mode complete: loaded {len(loaded_files)} file(s), {len(ansible_facts)} variable(s)")

        # Environment mode implementation
        elif mode == "environment":
            environment = args.get("environment")
            common = args.get("common")  # Defaults to 'base' via argument spec
            strict = args.get("strict", False)
            verbosity = args.get("verbosity", 0)

            display.vv(f"Environment mode: loading environment '{environment}' from root '{root}'")
            display.vvv(f"Hierarchical loading: {common} (common) → {environment} (environment-specific)")

            loaded_files = []
            ansible_facts = {}

            # Load common directory files first
            common_path = os.path.join(root, common)
            display.vv(f"Loading common environment: {common} from {root}")
            display.vvv(f"Searching for common files in: {common_path}")

            # Build patterns for common directory
            common_patterns = [
                os.path.join(common_path, '*.yml'),
                os.path.join(common_path, '*.yaml'),
                os.path.join(common_path, '*.json'),
            ]

            # Glob all matching files in common directory
            common_files = []
            for pattern_str in common_patterns:
                found = glob.glob(pattern_str)
                if found:
                    display.vvv(f"Common pattern '{pattern_str}' matched {len(found)} file(s)")
                common_files.extend(found)

            # Sort for deterministic order
            common_files = sorted(set(common_files))

            if common_files:
                display.vv(f"Found {len(common_files)} common file(s) in {common}/")
                display.vvv(f"Common files: {', '.join(common_files)}")
            else:
                display.vvv(f"No common files found in {common}/")

            # Load variables from each common file
            for vars_file in common_files:
                if verbosity >= 1:
                    display.v(f"Loading common variables from: {vars_file}")

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

            # Log common loading summary
            common_var_count = len(ansible_facts)
            if common_files:
                display.vv(f"Loaded {len(common_files)} common file(s) with {common_var_count} variable(s)")
                display.vvv(f"Common variables loaded: {', '.join(sorted(ansible_facts.keys())[:10])}{'...' if common_var_count > 10 else ''}")

            # Load environment-specific directory files (these override common)
            env_path = os.path.join(root, environment)
            display.vv(f"Loading environment-specific files from: {environment}")
            display.vvv(f"Searching for environment files in: {env_path}")

            # Build patterns for environment directory
            env_patterns = [
                os.path.join(env_path, '*.yml'),
                os.path.join(env_path, '*.yaml'),
                os.path.join(env_path, '*.json'),
            ]

            # Glob all matching files in environment directory
            env_files = []
            for pattern_str in env_patterns:
                found = glob.glob(pattern_str)
                if found:
                    display.vvv(f"Environment pattern '{pattern_str}' matched {len(found)} file(s)")
                env_files.extend(found)

            # Sort for deterministic order
            env_files = sorted(set(env_files))

            if env_files:
                display.vv(f"Found {len(env_files)} environment-specific file(s) in {environment}/")
                display.vvv(f"Environment files: {', '.join(env_files)}")
            else:
                display.vvv(f"No environment-specific files found in {environment}/")

            # Handle strict mode - fail if neither common nor environment files found
            if strict and len(common_files) == 0 and len(env_files) == 0:
                result["failed"] = True
                result["msg"] = f"In strict mode, variables files should be matched in the given directory: {root}/{environment}"
                return result

            # Warn if no files found in non-strict mode
            if not strict and len(common_files) == 0 and len(env_files) == 0:
                display.warning(f"No files found in common directory '{common}' or environment directory '{environment}'")
                display.vv("No files to load in environment mode")

            # Load variables from each environment file (these override common vars)
            for vars_file in env_files:
                if verbosity >= 1:
                    display.v(f"Loading environment-specific variables from: {vars_file}")

                # Track which variables might be overridden
                vars_before_load = set(ansible_facts.keys())

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
                # These will override any common variables with the same name
                if "ansible_facts" in include_vars_result:
                    new_vars = include_vars_result["ansible_facts"]
                    overridden_vars = set(new_vars.keys()) & vars_before_load
                    if overridden_vars and verbosity >= 3:
                        display.vvv(f"Environment-specific variables overriding common: {', '.join(sorted(overridden_vars))}")
                    ansible_facts.update(new_vars)
                    loaded_files.append(vars_file)

            # Update result with all loaded variables
            result["ansible_facts"] = ansible_facts
            result["loaded_files"] = sorted(loaded_files)
            result["variables_loaded"] = len(ansible_facts)
            result["msg"] = f"Loaded variables from {len(loaded_files)} file(s) in environment mode"

            # Hierarchical loading summary
            total_vars = len(ansible_facts)
            common_file_count = len(common_files)
            env_file_count = len(env_files)
            display.v(f"Environment mode complete: loaded {len(loaded_files)} file(s) ({common_file_count} common + {env_file_count} environment), {total_vars} total variable(s)")
            display.vvv(f"Hierarchical merge complete: {common} → {environment}")

        return result
