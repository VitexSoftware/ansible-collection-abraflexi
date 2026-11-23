#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: record
short_description: Manage a record of any AbraFlexi evidence
version_added: "1.0.0"
description:
  - Creates, updates or deletes one record.
  - Only fields given in O(data) are compared and written; other fields are left alone.
  - The server silently ignores unknown fields, so field names are checked against the evidence metadata first.
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
  state:
    description: Whether the record should exist.
    type: str
    choices: [present, absent]
    default: present
  data:
    description:
      - Field values as documented for the evidence.
      - Relations are written as V(code:XYZ), a numeric id, or V(ext:...).
      - The C(stitky) (labels) field is treated as the complete set of labels.
      - A list of dictionaries is a sub-item collection, such as C(polozkyFaktury).
    type: dict
    default: {}
  subitems_match:
    description:
      - Maps a sub-item collection name to the item field identifying an item.
      - Required to update sub-items of an existing record. Items not listed are kept.
    type: dict
    default: {}
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Ensure a customer exists
  vitexus.abraflexi.record:
    url: https://flexibee.example.com:5434
    company: demo
    login: admin
    password: "{{ abraflexi_password }}"
    evidence: adresar
    code: ACME
    data:
      nazev: ACME s.r.o.
      stat: code:CZ
      stitky: [VIP]

- name: Remove the customer
  vitexus.abraflexi.record:
    evidence: adresar
    code: ACME
    state: absent
"""

RETURN = r"""
id:
  description: Numeric identifier of the record, if it exists.
  returned: when known
  type: int
record:
  description: The record after the change.
  returned: when O(state=present) and the record exists
  type: dict
changes:
  description: Fields written, or to be written in check mode.
  returned: when O(state=present)
  type: dict
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    build_payload,
    check_fields,
    diff_record,
    fetch_record,
    get_properties,
    get_relations,
    identity_spec,
    is_items,
    jsonable,
    make_client,
    make_module,
    record_key,
    run,
)


def ensure_absent(module, evidence, current):
    if current is None:
        module.exit_json(changed=False)
    if not module.check_mode:
        run(module, lambda: make_client(module.params, evidence, current["id"]).delete())
    module.exit_json(changed=True, id=int(current["id"]),
                     diff=dict(before=dict(id=current["id"], kod=current.get("kod")), after={}))


def main():
    spec = identity_spec()
    spec.update(
        evidence=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        data=dict(type="dict", default={}),
        subitems_match=dict(type="dict", default={}),
    )
    module = make_module(spec, required_one_of=[("id", "code", "external_id")],
                         mutually_exclusive=[("id", "code"), ("id", "external_id")])
    params = module.params
    evidence = params["evidence"]
    keys = record_key(params)
    data = dict(params["data"])
    items = [name for name, value in data.items() if is_items(value)]

    current = run(module, lambda: fetch_record(params, evidence, keys, relations=items))
    if params["state"] == "absent":
        ensure_absent(module, evidence, current)

    properties = run(module, lambda: get_properties(params, evidence))
    relations = run(module, lambda: get_relations(params, evidence))
    problems = check_fields(data, properties, relations)
    if problems:
        module.fail_json(msg="Invalid data for %s: %s" % (evidence, "; ".join(problems)))

    ext = next((k for k in keys if k.startswith("ext:")), None)
    code = next((k[5:] for k in keys if k.startswith("code:")), None)
    if code and "kod" in properties and properties["kod"].get("isWritable") != "false":
        if data.setdefault("kod", code) != code and current is None:
            module.fail_json(msg="code and data.kod differ")

    if current is None:
        if params["id"] is not None:
            module.fail_json(msg="Record %s not found; a record cannot be created with a given id" % params["id"])
        changes = data
        payload = build_payload(data)
        payload.pop("stitky@removeAll", None)
        if ext:
            payload["id"] = [ext]
    else:
        changes = run(module, lambda: diff_record(data, current, properties, params["subitems_match"]))
        payload = build_payload(changes)
        identifiers = [current["id"]]
        if ext and ext not in (current.get("external-ids") or []):
            identifiers.append(ext)
            changes = dict(changes, **{"external-ids": [ext]})
        payload["id"] = identifiers if len(identifiers) > 1 else identifiers[0]

    changed = current is None or bool(changes)
    result = dict(changed=changed, changes=jsonable(changes))
    result["diff"] = dict(
        before=jsonable(dict((k, (current or {}).get(k)) for k in changes) if current else {}),
        after=jsonable(changes))

    record = current
    if changed and not module.check_mode:
        if current is None:
            rows = run(module, lambda: make_client(params, evidence).insert_to_abraflexi(payload))
        else:
            rows = run(module, lambda: make_client(params, evidence).update(payload))
        new_id = rows[0].get("id") if isinstance(rows, list) and rows else (current or {}).get("id")
        record = run(module, lambda: fetch_record(params, evidence, [new_id] if new_id else keys, relations=items))
    if record:
        result.update(id=int(record["id"]), record=jsonable(record))
    module.exit_json(**result)


if __name__ == "__main__":
    main()
