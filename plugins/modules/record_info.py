#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: record_info
short_description: Read records of any AbraFlexi evidence
version_added: "1.0.0"
description:
  - Returns one record by its identifier or a list of records matching a filter.
  - A missing record yields an empty list.
extends_documentation_fragment:
  - vitexus.abraflexi.abraflexi
  - vitexus.abraflexi.abraflexi.company
options:
  evidence:
    description: Evidence name, for example V(adresar) or V(faktura-vydana).
    type: str
    required: true
  id:
    description: Numeric identifier of the record.
    type: int
  code:
    description: Code (C(kod)) of the record.
    type: str
  external_id:
    description: External identifier, with or without the C(ext:) prefix.
    type: str
  filter:
    description: AbraFlexi filter expression, for example V(stat = 'code:CZ').
    type: str
  detail:
    description: Detail level such as V(id), V(summary), V(full) or V(custom:kod,nazev).
    type: str
    default: summary
  relations:
    description: Sub-evidences to include.
    type: list
    elements: str
    default: []
  order:
    description: Field to sort by.
    type: str
  order_direction:
    description: Sort direction.
    type: str
    choices: [asc, desc]
    default: asc
  limit:
    description: Maximum number of records; V(0) reads all of them.
    type: int
    default: 20
  start:
    description: Offset of the first record.
    type: int
    default: 0
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Find unpaid invoices
  vitexus.abraflexi.record_info:
    evidence: faktura-vydana
    filter: "stavUhrK is null"
    detail: custom:kod,sumCelkem
    limit: 0
  register: unpaid
"""

RETURN = r"""
records:
  description: Records found.
  returned: success
  type: list
  elements: dict
row_count:
  description: Number of matching records regardless of O(limit).
  returned: when listing
  type: int
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    as_list,
    fetch_record,
    identity_spec,
    jsonable,
    make_client,
    make_module,
    record_key,
    run,
)


def main():
    spec = identity_spec()
    spec.update(
        evidence=dict(type="str", required=True),
        filter=dict(type="str"),
        detail=dict(type="str", default="summary"),
        relations=dict(type="list", elements="str", default=[]),
        order=dict(type="str"),
        order_direction=dict(type="str", choices=["asc", "desc"], default="asc"),
        limit=dict(type="int", default=20),
        start=dict(type="int", default=0),
    )
    module = make_module(spec, mutually_exclusive=[("id", "code", "external_id", "filter")])
    params = module.params
    evidence = params["evidence"]
    keys = record_key(params)
    if keys:
        record = run(module, lambda: fetch_record(params, evidence, keys, params["detail"], params["relations"]))
        module.exit_json(changed=False, records=jsonable([record] if record else []))

    query = {"detail": params["detail"], "limit": params["limit"], "start": params["start"],
             "add-row-count": "true"}
    if params["relations"]:
        query["relations"] = ",".join(params["relations"])
    if params["order"]:
        query["order"] = "%s@%s" % (params["order"], "D" if params["order_direction"] == "desc" else "A")
    client = run(module, lambda: make_client(params, evidence, query=query, filter_expr=params["filter"]))
    rows = run(module, client.perform_request)
    module.exit_json(changed=False, records=jsonable(as_list(rows)), row_count=client.row_count)


if __name__ == "__main__":
    main()
