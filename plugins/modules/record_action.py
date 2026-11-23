#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: record_action
short_description: Lock, unlock or cancel an AbraFlexi record
version_added: "1.0.0"
description:
  - Performs a record action only if the record is not already in the resulting state.
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
  action:
    description:
      - Action to perform.
      - V(storno) cannot be reverted.
    type: str
    required: true
    choices: [lock, lock-for-ucetni, unlock, storno]
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Lock an invoice
  vitexus.abraflexi.record_action:
    evidence: faktura-vydana
    code: VF1-0001/2026
    action: lock
"""

RETURN = r"""
id:
  description: Numeric identifier of the record.
  returned: success
  type: int
"""

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    identity_spec,
    make_client,
    make_module,
    must_fetch,
    run,
)


LOCKS = {
    "lock": ("zamek.zamceno",),
    "lock-for-ucetni": ("zamek.polozamceno",),
    # "seen" records are not locked either
    "unlock": ("zamek.otevreno", "zamek.prohlednuto"),
}


def main():
    spec = identity_spec()
    spec.update(
        evidence=dict(type="str", required=True),
        action=dict(type="str", required=True, choices=["lock", "lock-for-ucetni", "unlock", "storno"]),
    )
    module = make_module(spec, required_one_of=[("id", "code", "external_id")])
    params = module.params
    action = params["action"]
    record = must_fetch(module, params["evidence"])
    field = "storno" if action == "storno" else "zamekK"
    if field not in record:
        module.fail_json(msg="Evidence %s does not support action %s" % (params["evidence"], action))
    before = record[field]
    done = before == "true" if action == "storno" else before in LOCKS[action]
    if not done and not module.check_mode:
        client = make_client(params, params["evidence"], record["id"])
        run(module, lambda: client._send_evidence_action(action))
    after = before if done else ("true" if action == "storno" else LOCKS[action][0])
    module.exit_json(changed=not done, id=int(record["id"]),
                     diff=dict(before={field: before}, after={field: after}))


if __name__ == "__main__":
    main()
