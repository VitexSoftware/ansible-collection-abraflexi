# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
name: companies
short_description: AbraFlexi companies as inventory hosts
version_added: "1.0.0"
description:
  - Creates one host per AbraFlexi company, so that a play can be run over all of them.
  - Hosts use the local connection and have the C(abraflexi_company) and C(abraflexi_url) variables.
  - The configuration file name must end with C(abraflexi.yml) or C(abraflexi.yaml).
extends_documentation_fragment:
  - constructed
options:
  plugin:
    description: Plugin name.
    type: str
    required: true
    choices: [vitexus.abraflexi.companies]
  group:
    description: Group for all the companies.
    type: str
    default: abraflexi_companies
  url:
    description: Server URL.
    type: str
    required: true
    env: [{name: ABRAFLEXI_URL}]
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
# abraflexi.yml
plugin: vitexus.abraflexi.companies
url: https://flexibee.example.com:5434
groups:
  tracked: abraflexi.watchingChanges == 'true'
"""

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable

from ansible_collections.vitexus.abraflexi.plugins.module_utils.abraflexi import (
    AbraFlexiException,
    HAS_LIB,
    as_list,
    jsonable,
    make_client,
)


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = "vitexus.abraflexi.companies"

    def verify_file(self, path):
        return super().verify_file(path) and path.endswith(("abraflexi.yml", "abraflexi.yaml"))

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache)
        if not HAS_LIB:
            raise AnsibleParserError("The python_abraflexi library (python3-abraflexi) is required")
        self._read_config_data(path)
        names = ("url", "login", "password", "auth_session_id", "timeout", "validate_certs")
        params = dict((name, self.get_option(name)) for name in names)
        try:
            data = make_client(params)._perform_root_request("c.json")
        except (AbraFlexiException, ValueError) as exc:
            raise AnsibleParserError("AbraFlexi: %s" % exc)
        group = self.inventory.add_group(self.get_option("group"))
        strict = self.get_option("strict")
        for company in as_list((data.get("companies") or {}).get("company")):
            host = company["dbNazev"]
            self.inventory.add_host(host, group=group)
            hostvars = {
                "ansible_connection": "local",
                "ansible_python_interpreter": "{{ ansible_playbook_python }}",
                "abraflexi_company": host,
                "abraflexi_url": params["url"],
                "abraflexi": jsonable(company),
            }
            for name, value in hostvars.items():
                self.inventory.set_variable(host, name, value)
            self._set_composite_vars(self.get_option("compose"), hostvars, host, strict=strict)
            self._add_host_to_composed_groups(self.get_option("groups"), hostvars, host, strict=strict)
            self._add_host_to_keyed_groups(self.get_option("keyed_groups"), hostvars, host, strict=strict)
