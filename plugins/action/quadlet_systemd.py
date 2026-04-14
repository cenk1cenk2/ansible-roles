#!/usr/bin/env python3

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
    _VALID_ARGS = frozenset(("services", "triggers", "scope"))

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                services=dict(type="list", elements="raw", required=True),
                triggers=dict(type="list", elements="bool", default=[]),
                scope=dict(type="str", default="system"),
            ),
        )

        result = super().run(tmp, task_vars)
        result.update(changed=False, services=[])

        triggered = any(args["triggers"]) if args["triggers"] else False
        default_scope = args["scope"]

        display.v(f"Daemon reload (scope={default_scope})")

        reload_result = self._execute_module(
            module_name="ansible.builtin.systemd",
            module_args={"daemon_reload": True, "scope": default_scope},
            task_vars=task_vars,
        )

        if reload_result.get("failed"):
            result["failed"] = True
            result["msg"] = f"daemon_reload failed: {reload_result.get('msg', '')}"

            return result

        for svc in args["services"]:
            if isinstance(svc, str):
                svc = {"name": svc}

            name = svc["name"]
            scope = svc.get("scope", default_scope)
            raw_state = svc.get("state", "reloaded")

            if raw_state == "reloaded":
                state = "restarted" if triggered else "started"
            else:
                state = raw_state

            display.v(f"Service '{name}': state={state} (raw={raw_state}, triggered={triggered})")

            svc_result = self._execute_module(
                module_name="ansible.builtin.systemd",
                module_args={"name": name, "state": state, "scope": scope},
                task_vars=task_vars,
            )

            if svc_result.get("failed"):
                result["failed"] = True
                result["msg"] = f"Failed to set state for '{name}': {svc_result.get('msg', '')}"

                return result

            if svc_result.get("changed"):
                result["changed"] = True

            result["services"].append({"name": name, "state": state, "changed": svc_result.get("changed", False)})

        svc_names = [s["name"] for s in result["services"]]
        result["triggered"] = triggered
        result["msg"] = f"Processed {', '.join(svc_names)} (triggered={triggered})"
        display.v(result["msg"])

        return result
