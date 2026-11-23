===========================
vitexus.abraflexi changelog
===========================

v1.0.2
======

- Added the role README required by Ansible Galaxy.

v1.0.1
======

- Security: ``companies`` inventory does not template server data, validates names and prefixes hosts (``host_prefix``).
- Security: ``report`` creates files with mode 0600 and accepts file attributes.
- Security: empty ``code`` and ``external_id`` are rejected.
- ``abraflexi_server_network_mode`` added.

v1.0.0
======

- Initial version: modules, ``record`` lookup, ``companies`` inventory and the ``abraflexi_server`` role.
