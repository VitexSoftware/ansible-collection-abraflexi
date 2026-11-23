#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: attachment
short_description: Manage attachments of an AbraFlexi record
version_added: "1.0.0"
description:
  - Uploads or removes a file attached to a record.
  - A file is matched by name and compared by content.
  - The server appends a file extension of its own to some names (V(a.txt) is stored as V(a.txt.txt)); such names match too.
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
  name:
    description: Attachment name. Defaults to the base name of O(src).
    type: str
  src:
    description: File on the host running the module. Required when O(state=present).
    type: path
  content_type:
    description: MIME type; guessed from the name by default.
    type: str
  state:
    description: Whether the attachment should exist.
    type: str
    choices: [present, absent]
    default: present
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Attach a contract
  vitexus.abraflexi.attachment:
    evidence: adresar
    code: ACME
    src: /srv/contracts/acme.pdf
"""

RETURN = r"""
attachment_id:
  description: Identifier of the attachment.
  returned: when it exists
  type: int
"""

import mimetypes
import os

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    as_list,
    identity_spec,
    make_client,
    make_module,
    must_fetch,
    run,
)


def main():
    spec = identity_spec()
    spec.update(
        evidence=dict(type="str", required=True),
        name=dict(type="str"),
        src=dict(type="path"),
        content_type=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module = make_module(spec, required_one_of=[("id", "code", "external_id"), ("name", "src")],
                         required_if=[("state", "present", ("src",))])
    params = module.params
    name = params["name"] or os.path.basename(params["src"])
    present = params["state"] == "present"
    content = b""
    if present:
        try:
            with open(params["src"], "rb") as handle:
                content = handle.read()
        except OSError as exc:
            module.fail_json(msg="Cannot read %s: %s" % (params["src"], exc))

    record = must_fetch(module, params["evidence"], detail="id")

    def client():
        return make_client(params, params["evidence"], record["id"])

    extension = os.path.splitext(name)[1]
    names = (name, name + extension)
    found = [a for a in as_list(run(module, client().list_attachments)) if a.get("nazSoub") in names]
    keep = None
    if present:
        for item in found:
            if run(module, lambda: client().download_attachment(item["id"])) == content:
                keep = item
                break
    remove = [a for a in found if a is not keep]
    upload = present and keep is None
    result = dict(changed=bool(remove or upload))
    if keep:
        result["attachment_id"] = int(keep["id"])
    if not module.check_mode:
        if upload:
            ctype = params["content_type"] or mimetypes.guess_type(name)[0] or "application/octet-stream"
            result["attachment_id"] = run(module, lambda: client().add_attachment(name, content, ctype))
            if not result["attachment_id"]:
                module.fail_json(msg="The server did not confirm the upload")
        for item in remove:
            run(module, lambda: client().delete_attachment(item["id"]))
    module.exit_json(**result)


if __name__ == "__main__":
    main()
