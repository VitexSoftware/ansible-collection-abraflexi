# abraflexi_server

Installs the AbraFlexi server from repo.vitexsoftware.com on Debian 12/13 and Ubuntu 24.04.

```yaml
- hosts: abraflexi
  become: true
  roles:
    - role: vitexus.abraflexi.abraflexi_server
```

| Variable | Default | Meaning |
|---|---|---|
| `abraflexi_server_variant` | `flexibee` | `flexibee` or `abraflexi-server` |
| `abraflexi_server_version` | empty | exact package version |
| `abraflexi_server_hold` | `false` | hold the package |
| `abraflexi_server_network_mode` | `network` | installer answer, `network` or `local` |
| `abraflexi_server_backup_enabled` | `false` | daily backups, `flexibee` variant only |
| `abraflexi_server_backup_dir` | `/var/backups/abraflexi` | backup directory |

Other variables are in `defaults/main.yml`. Restrict access to port 5434 until the first administrator
exists; the role does not configure a firewall.
