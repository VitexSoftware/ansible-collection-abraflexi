#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: report
short_description: Export an AbraFlexi report to a file
version_added: "1.0.0"
description:
  - Exports a printable report of a record, or of the whole evidence, to a file on the host running the module.
  - PDF output contains its creation time, so an existing file is only rewritten with O(force=true).
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
  dest:
    description: Destination file.
    type: path
    required: true
  format:
    description: Output format.
    type: str
    choices: [pdf, xls]
    default: pdf
  report_name:
    description: Report identifier, see M(vitexus.abraflexi.evidence_info).
    type: str
  language:
    description: Report language.
    type: str
    choices: [cs, sk, en, de]
  force:
    description: Overwrite an existing file.
    type: bool
    default: false
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Save an invoice as PDF
  vitexus.abraflexi.report:
    evidence: faktura-vydana
    code: VF1-0001/2026
    dest: /srv/invoices/VF1-0001.pdf
"""

RETURN = r"""
dest:
  description: Path of the file.
  returned: success
  type: str
size:
  description: Size of the exported file.
  returned: when exported
  type: int
"""

import os
import tempfile

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
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
        dest=dict(type="path", required=True),
        format=dict(type="str", choices=["pdf", "xls"], default="pdf"),
        report_name=dict(type="str"),
        language=dict(type="str", choices=["cs", "sk", "en", "de"]),
        force=dict(type="bool", default=False),
    )
    module = make_module(spec, mutually_exclusive=[("id", "code", "external_id")])
    params = module.params
    dest = params["dest"]
    if os.path.isdir(dest):
        module.fail_json(msg="%s is a directory" % dest)
    if os.path.exists(dest) and not params["force"]:
        module.exit_json(changed=False, dest=dest)
    record_id = None
    if params["id"] is not None or params["code"] or params["external_id"]:
        record_id = must_fetch(module, params["evidence"], detail="id")["id"]
    if module.check_mode:
        module.exit_json(changed=True, dest=dest)
    client = make_client(params, params["evidence"])
    content = run(module, lambda: client.export_report(
        record_id, params["format"], params["report_name"], params["language"]))
    if not isinstance(content, bytes) or (params["format"] == "pdf" and not content.startswith(b"%PDF")):
        module.fail_json(msg="The server did not return a %s report" % params["format"])
    handle, tmp = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(handle, "wb") as out:
        out.write(content)
    module.atomic_move(tmp, dest)
    module.exit_json(changed=True, dest=dest, size=len(content))


if __name__ == "__main__":
    main()
