#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: server_info
short_description: Get AbraFlexi server status
version_added: "1.0.0"
description:
  - Returns version, license and load of the server.
extends_documentation_fragment:
  - vitexus.abraflexi.abraflexi
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Get the server version
  vitexus.abraflexi.server_info:
  register: server
"""

RETURN = r"""
status:
  description: Server status, including C(version).
  returned: success
  type: dict
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    jsonable,
    make_client,
    make_module,
    run,
)


def main():
    module = make_module(company=False)
    data = run(module, lambda: make_client(module.params)._perform_root_request("status.json"))
    module.exit_json(changed=False, status=jsonable(data.get("status", data)))


if __name__ == "__main__":
    main()
