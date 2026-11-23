#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: changes
short_description: Enable or disable the AbraFlexi Changes API
version_added: "1.0.0"
description:
  - Controls change tracking of a company. Web hooks depend on it.
extends_documentation_fragment:
  - vitexus.abraflexi.abraflexi
  - vitexus.abraflexi.abraflexi.company
options:
  state:
    description: Desired state.
    type: str
    choices: [enabled, disabled]
    default: enabled
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Track changes
  vitexus.abraflexi.changes:
    state: enabled
"""

RETURN = r"""
enabled:
  description: Resulting state.
  returned: success
  type: bool
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    make_client,
    make_module,
    run,
)


def is_enabled(module):
    data = run(module, lambda: make_client(module.params, "changes").perform_request("status.json"))
    if isinstance(data, dict):
        data = data.get("winstrom", data).get("message", "")
    text = str(data).lower()
    if "enabled" in text or text == "true":
        return True
    if "disabled" in text or text == "false":
        return False
    module.fail_json(msg="Unexpected Changes API status: %s" % data)


def main():
    module = make_module(dict(state=dict(type="str", choices=["enabled", "disabled"], default="enabled")))
    wanted = module.params["state"] == "enabled"
    changed = is_enabled(module) != wanted
    if changed and not module.check_mode:
        action = "enable.json" if wanted else "disable.json"
        run(module, lambda: make_client(module.params, "changes").perform_request(action, "PUT"))
        if is_enabled(module) != wanted:
            module.fail_json(msg="The server did not change the Changes API status")
    module.exit_json(changed=changed, enabled=wanted)


if __name__ == "__main__":
    main()
