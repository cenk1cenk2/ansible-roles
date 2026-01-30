from __future__ import annotations

__metaclass__ = type

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

        result = super(ActionModule, self).run(tmp, task_vars)

        result.update(dict(changed=False, failed=False, msg="", skipped=False))

        return result
