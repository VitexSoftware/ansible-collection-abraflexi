#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: label
short_description: Manage labels of an AbraFlexi record
version_added: "1.0.0"
description:
  - Adds, removes or replaces labels (C(stitky)) of a record. The labels must exist in the V(stitek) evidence.
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
  labels:
    description: Label codes.
    type: list
    elements: str
    required: true
  state:
    description: V(present) adds, V(absent) removes, V(exact) replaces all labels.
    type: str
    choices: [present, absent, exact]
    default: present
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Mark a customer
  vitexus.abraflexi.label:
    evidence: adresar
    code: ACME
    labels: [VIP]
"""

RETURN = r"""
labels:
  description: Resulting labels.
  returned: success
  type: list
  elements: str
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    build_payload,
    identity_spec,
    labels,
    make_client,
    make_module,
    must_fetch,
    run,
)


def main():
    spec = identity_spec()
    spec.update(
        evidence=dict(type="str", required=True),
        labels=dict(type="list", elements="str", required=True),
        state=dict(type="str", choices=["present", "absent", "exact"], default="present"),
    )
    module = make_module(spec, required_one_of=[("id", "code", "external_id")])
    params = module.params
    record = must_fetch(module, params["evidence"])
    if "stitky" not in record:
        module.fail_json(msg="Evidence %s does not support labels" % params["evidence"])
    before = labels(record["stitky"])
    given = set(labels(params["labels"]))
    if params["state"] == "present":
        after = sorted(set(before) | given)
    elif params["state"] == "absent":
        after = sorted(set(before) - given)
    else:
        after = sorted(given)
    changed = before != after
    if changed and not module.check_mode:
        payload = build_payload({"stitky": after})
        payload["id"] = record["id"]
        run(module, lambda: make_client(params, params["evidence"]).update(payload))
    module.exit_json(changed=changed, labels=after, diff=dict(before=dict(labels=before), after=dict(labels=after)))


if __name__ == "__main__":
    main()
