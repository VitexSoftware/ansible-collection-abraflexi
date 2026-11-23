#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: webhook
short_description: Manage AbraFlexi web hooks
version_added: "1.0.0"
description:
  - Registers or removes a web hook of a company, identified by its target URL.
  - The Changes API must be enabled.
extends_documentation_fragment:
  - vitexus.abraflexi.abraflexi
  - vitexus.abraflexi.abraflexi.company
options:
  hook_url:
    description: URL called by AbraFlexi.
    type: str
    required: true
  format:
    description: Data format.
    type: str
    choices: [JSON, XML]
    default: JSON
  secret:
    description: Secret sent with every call. Used at registration only.
    type: str
  skip_url_test:
    description: Do not test the URL at registration.
    type: bool
    default: false
  state:
    description: Whether the hook should exist.
    type: str
    choices: [present, absent]
    default: present
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Register a web hook
  vitexus.abraflexi.webhook:
    hook_url: https://example.com/webhook
"""

RETURN = r"""
id:
  description: Identifier of the hook.
  returned: when it exists
  type: int
"""

from urllib.parse import quote_plus

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    AbraFlexiException,
    as_list,
    make_client,
    make_module,
    run,
)


def hooks(module):
    rows = as_list(run(module, lambda: make_client(module.params, "hooks").perform_request()))
    return [h for h in rows if isinstance(h, dict) and h.get("url") == module.params["hook_url"]]


def register(module):
    query = {"url": module.params["hook_url"], "format": module.params["format"]}
    if module.params["secret"]:
        query["secKey"] = module.params["secret"]
    if module.params["skip_url_test"]:
        query["skipUrlTest"] = "true"
    try:
        make_client(module.params, "hooks", query=query).perform_request("", "PUT")
    except AbraFlexiException as exc:
        # no_log does not cover the URL-encoded form of the secret
        text = str(exc)
        if module.params["secret"]:
            text = text.replace(quote_plus(module.params["secret"]), "***")
        module.fail_json(msg="Cannot register the web hook: %s" % text)


def main():
    module = make_module(dict(
        hook_url=dict(type="str", required=True),
        format=dict(type="str", choices=["JSON", "XML"], default="JSON"),
        secret=dict(type="str", no_log=True),
        skip_url_test=dict(type="bool", default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    ))
    found = hooks(module)
    if module.params["state"] == "present":
        keep = [h for h in found if h.get("dataFormat", "").upper() == module.params["format"]]
        remove = [h for h in found if h not in keep]
    else:
        keep, remove = [], found
    create = module.params["state"] == "present" and not keep
    if not module.check_mode:
        for hook in remove:
            run(module, lambda: make_client(module.params, "hooks").perform_request("%s.json" % hook["id"], "DELETE"))
        if create:
            register(module)
            keep = hooks(module)
            if not keep:
                module.fail_json(msg="The web hook is not registered although the server reported success")
    result = dict(changed=bool(create or remove))
    if keep:
        result["id"] = int(keep[0]["id"])
    module.exit_json(**result)


if __name__ == "__main__":
    main()
