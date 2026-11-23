# Ansible collection vitexus.abraflexi

Works with the AbraFlexi (FlexiBee) REST API through
[python-abraflexi](https://github.com/VitexSoftware/python-abraflexi) and installs the AbraFlexi server.

## Requirements

- ansible-core 2.16+
- `python3-abraflexi` on the host running the modules (usually the controller, `connection: local`).
  The inventory and lookup plugins need it in the Python environment Ansible itself runs in.

## Content

| Name | Purpose |
|---|---|
| `record` | create, update, delete a record of any evidence |
| `record_info` | read records |
| `record_action` | lock, unlock, storno |
| `attachment`, `report`, `label` | attachments, PDF/XLS export, labels |
| `changes`, `webhook` | Changes API and web hooks |
| `server_info`, `company_info`, `evidence_info` | information |
| lookup `record` | read a record in a template |
| inventory `companies` | one host per company |
| role `abraflexi_server` | install the server |

Documentation: `ansible-doc vitexus.abraflexi.record`.

## Connection

Use module options or `ABRAFLEXI_URL`, `ABRAFLEXI_COMPANY`, `ABRAFLEXI_LOGIN`, `ABRAFLEXI_PASSWORD`.
Certificates are verified by default; set `validate_certs: false` for self-signed ones.

```yaml
- hosts: localhost
  connection: local
  module_defaults:
    group/vitexus.abraflexi.abraflexi:
      url: https://flexibee.example.com:5434
      company: demo
      login: admin
      password: "{{ vault_abraflexi_password }}"
  tasks:
    - vitexus.abraflexi.record:
        evidence: adresar
        code: ACME
        data:
          nazev: ACME s.r.o.
```

Unknown fields are rejected (the server itself ignores them silently). Sub-items of an existing document
are only updated with `subitems_match`, which names the field identifying an item. Check mode never writes.

## Role abraflexi_server

See `roles/abraflexi_server/defaults/main.yml`. `abraflexi_server_variant` selects the package:

- `flexibee` (default): current build from the `borrow` suite of repo.vitexsoftware.com; supports backups
- `abraflexi-server`: 2022.5.5 from the distribution suite, without backups

**Restrict access to port 5434 until the first administrator exists.** The role installs a network server
(`abraflexi_server_network_mode`) and does not configure a firewall.

## Tests

```sh
python3 -m pytest tests/unit                  # from ansible_collections/vitexus/abraflexi
ansible-playbook -i localhost, tests/integration/site.yml   # needs ABRAFLEXI_* and ABRAFLEXI_TEST_COMPANY
```

## License

Plugins GPL-3.0-or-later, the rest MIT.
