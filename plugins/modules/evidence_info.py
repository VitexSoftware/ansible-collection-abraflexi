#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: evidence_info
short_description: Describe AbraFlexi evidences
version_added: "1.0.0"
description:
  - Lists evidences, or returns fields, relations and reports of one evidence.
extends_documentation_fragment:
  - vitexus.abraflexi.abraflexi
  - vitexus.abraflexi.abraflexi.company
options:
  evidence:
    description: Evidence to describe. All evidences are listed when omitted.
    type: str
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Describe the address book
  vitexus.abraflexi.evidence_info:
    evidence: adresar
"""

RETURN = r"""
evidences:
  description: Evidences of the company.
  returned: when O(evidence) is omitted
  type: list
  elements: dict
properties:
  description: Fields by name.
  returned: when O(evidence) is given
  type: dict
relations:
  description: Sub-evidence names.
  returned: when O(evidence) is given
  type: list
  elements: str
reports:
  description: Reports.
  returned: when O(evidence) is given
  type: list
  elements: dict
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    as_list,
    get_properties,
    get_relations,
    jsonable,
    make_client,
    make_module,
    run,
)


def main():
    module = make_module(dict(evidence=dict(type="str")))
    params = module.params
    evidence = params["evidence"]
    if not evidence:
        data = run(module, lambda: make_client(params).perform_request("evidence-list.json"))
        rows = as_list((data.get("evidences") or {}).get("evidence"))
        module.exit_json(changed=False, evidences=jsonable(rows))
    properties = run(module, lambda: get_properties(params, evidence))
    relations = run(module, lambda: get_relations(params, evidence))
    reports = run(module, lambda: make_client(params, evidence).get_reports())
    reports = as_list((reports.get("reports") or {}).get("report")) if isinstance(reports, dict) else []
    module.exit_json(changed=False, properties=jsonable(properties), relations=relations, reports=jsonable(reports))


if __name__ == "__main__":
    main()
