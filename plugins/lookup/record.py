# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
name: record
short_description: Read AbraFlexi records
version_added: "1.0.0"
description:
  - Returns one record for every given identifier. Runs on the controller.
options:
  _terms:
    description: Record identifiers such as V(code:ACME), V(ext:shop:1) or a numeric id.
    required: true
  evidence:
    description: Evidence name.
    type: str
    required: true
  detail:
    description: Detail level.
    type: str
    default: full
  url:
    description: Server URL.
    type: str
    required: true
    env: [{name: ABRAFLEXI_URL}]
  company:
    description: Company database identifier.
    type: str
    required: true
    env: [{name: ABRAFLEXI_COMPANY}]
  login:
    description: User name.
    type: str
    env: [{name: ABRAFLEXI_LOGIN}]
  password:
    description: Password.
    type: str
    env: [{name: ABRAFLEXI_PASSWORD}]
  auth_session_id:
    description: Session token.
    type: str
    env: [{name: ABRAFLEXI_AUTHSESSID}]
  timeout:
    description: Request timeout in seconds.
    type: int
    default: 60
  validate_certs:
    description: Whether to verify the TLS certificate.
    type: bool
    default: true
requirements:
  - python3-abraflexi
author:
  - Vitex Software (@VitexSoftware)
"""

EXAMPLES = r"""
- name: Show a customer name
  ansible.builtin.debug:
    msg: "{{ lookup('vitexus.abraflexi.record', 'code:ACME', evidence='adresar').nazev }}"
"""

RETURN = r"""
_raw:
  description: Records found.
  type: list
  elements: dict
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    AbraFlexiException,
    HAS_LIB,
    fetch_record,
    jsonable,
)


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        if not HAS_LIB:
            raise AnsibleError("The python_abraflexi library (python3-abraflexi) is required")
        self.set_options(var_options=variables, direct=kwargs)
        names = ("url", "company", "login", "password", "auth_session_id", "timeout", "validate_certs")
        params = dict((name, self.get_option(name)) for name in names)
        result = []
        for term in terms:
            try:
                record = fetch_record(params, self.get_option("evidence"), [str(term)], self.get_option("detail"))
            except (AbraFlexiException, ValueError) as exc:
                raise AnsibleError("AbraFlexi: %s" % exc)
            if record is None:
                raise AnsibleError("AbraFlexi record %s not found" % term)
            result.append(jsonable(record))
        return result
