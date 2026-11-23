#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: company_info
short_description: List AbraFlexi companies
version_added: "1.0.0"
description:
  - Returns companies accessible to the user.
extends_documentation_fragment:
  - vitexus.abraflexi.abraflexi
options:
  company:
    description: Only return the company with this database identifier.
    type: str
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: List companies
  vitexus.abraflexi.company_info:
"""

RETURN = r"""
companies:
  description: Companies; C(dbNazev) is the identifier used as O(company).
  returned: success
  type: list
  elements: dict
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    as_list,
    jsonable,
    make_client,
    make_module,
    run,
)


def main():
    module = make_module(dict(company=dict(type="str")), company=False)
    data = run(module, lambda: make_client(module.params)._perform_root_request("c.json"))
    rows = as_list((data.get("companies") or {}).get("company"))
    if module.params["company"]:
        rows = [r for r in rows if r.get("dbNazev") == module.params["company"]]
    module.exit_json(changed=False, companies=jsonable(rows))


if __name__ == "__main__":
    main()
