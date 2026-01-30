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

        return result
