# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  url:
    description:
      - AbraFlexi server URL including the port.
      - Falls back to the E(ABRAFLEXI_URL) environment variable.
    type: str
    required: true
  login:
    description: User name. Falls back to E(ABRAFLEXI_LOGIN).
    type: str
  password:
    description: Password. Falls back to E(ABRAFLEXI_PASSWORD).
    type: str
  auth_session_id:
    description: Session token used instead of O(login) and O(password). Falls back to E(ABRAFLEXI_AUTHSESSID).
    type: str
  timeout:
    description: Request timeout in seconds.
    type: int
    default: 60
  validate_certs:
    description:
      - Whether to verify the TLS certificate of the server.
      - AbraFlexi generates a self-signed certificate on installation.
    type: bool
    default: true
requirements:
  - python3-abraflexi (C(python_abraflexi) Python module) on the host running the module
"""

    COMPANY = r"""
options:
  company:
    description: Company database identifier. Falls back to E(ABRAFLEXI_COMPANY).
    type: str
    required: true
"""
