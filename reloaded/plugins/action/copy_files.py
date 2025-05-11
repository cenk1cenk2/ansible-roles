from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

__metaclass__ = type

display = Display()

class ActionModule(ActionBase):
    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = False

        _, args = self.validate_argument_spec(
            argument_spec=dict(
                at=dict(type="raw", default="Hello world!"),
                verbosity=dict(type="int", default=0),
            ),
        )

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp

        display.vv("Hello world!")

        result["changed"] = True
        result["failed"] = False
        result["msg"] = "yes hello"

        return result
