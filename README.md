# 📦 Post-Anonymization Secrets Populator

**Post-Anonymization Secrets Populator (PASP)** is a GitHub Action (and standalone Python tool) that runs after a
production database has been anonymized in a test environment. It safely inserts predefined secrets, plugin settings,
and environment-specific configuration into your database to prevent test environments from pushing to real production
APIs.

This tool reads a YAML configuration file that describes which rows to insert or update in specified database tables.

---

## 🚀 Use Case

When you copy production data to a test or staging environment, sensitive credentials (e.g., API keys, webhook URLs,
SFTP settings) may still be present. This tool ensures test-safe replacements are inserted immediately after the
anonymization step.

---

## 🧰 Features

- 🔐 Prevents accidental use of production integrations in test environments
- ✅ Supports `INSERT ... ON DUPLICATE KEY UPDATE` for idempotency
- ⚙️ Optional `commit_strategy`:
    - `per_table`: Commit each table independently (safer, partial success)
    - `all_or_nothing`: Fail entire action if any table fails (default, transactional)
- 🧠 Binary UUIDs supported via `"0x..."` auto-conversion
- 📄 YAML config for defining table entries
- 🔌 Optional SSH tunnel via jump host using native OpenSSH (no `sshtunnel`/`paramiko`)
- 🐳 Docker-based GitHub Action
- 💾 MySQL support (PostgreSQL planned)

---

## 🛠️ Usage in GitHub Actions

### Example Workflow (no SSH tunnel)

```yaml
name: Post-Anonymization Setup

on:
  workflow_dispatch:

jobs:
  inject-test-config:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Inject test environment secrets
        uses: sanikapanika/post-anonymization-secrets-populator@v1
        with:
          db_host: ${{ secrets.DB_HOST }}
          db_port: ${{ secrets.DB_PORT }}
          db_name: ${{ secrets.DB_NAME }}
          db_user: ${{ secrets.DB_USER }}
          db_password: ${{ secrets.DB_PASSWORD }}
          config_file: test-env-config.yaml        # ✅ Required (lives in your project, check example-config.yaml for reference)
          commit_strategy: all_or_nothing          # optional: all_or_nothing (default) or per_table
```

### Example Workflow (with SSH tunnel)

```yaml
name: Post-Anonymization Setup

on:
  workflow_dispatch:

jobs:
  inject-test-config:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Inject test environment secrets
        uses: sanikapanika/post-anonymization-secrets-populator@v1
        with:
          db_host: ${{ secrets.DB_HOST }}
          db_port: ${{ secrets.DB_PORT }}
          db_name: ${{ secrets.DB_NAME }}
          db_user: ${{ secrets.DB_USER }}
          db_password: ${{ secrets.DB_PASSWORD }}
          config_file: test-env-config.yaml        # ✅ Required (lives in your project, check example-config.yaml for reference)
          commit_strategy: all_or_nothing          # optional: all_or_nothing (default) or per_table
          use_ssh_tunnel: true
          ssh_jump_host: ${{ secrets.SSH_JUMP_HOST }}  # Hostname or IP of the jump server
          ssh_jump_port: ${{ secrets.SSH_JUMP_PORT }}  # SSH port for the jump server (default: 22)
          ssh_jump_user: ${{ secrets.SSH_JUMP_USER }}  # SSH user for the jump server
          ssh_jump_key: ${{ secrets.SSH_JUMP_KEY }}    # Path to private SSH key (unencrypted or use ssh-agent)
          ssh_db_host: ${{ secrets.SSH_DB_HOST }}          # The tunnel target, your actual database server hostname/ip
          ssh_db_port: ${{ secrets.SSH_DB_PORT }}          # The tunnel target DB port,  (default: 3306)
```

Resulting effect is a handled SSH Bastion scenario, meaning that you have a tunnel through your jump server to your database server.

---

## 🔐 Inputs / Environment Variables

### Basic DB Access (direct)

| Name                  | Required | Description                               |
|-----------------------|----------|-------------------------------------------|
| INPUT_DB_HOST         | ✅        | Hostname of the MySQL database            |
| INPUT_DB_PORT         | ✅        | Port of the MySQL database                |
| INPUT_DB_NAME         | ✅        | Name of the database                      |
| INPUT_DB_USER         | ✅        | Database username                         |
| INPUT_DB_PASSWORD     | ✅        | Database password                         |
| INPUT_CONFIG_FILE     | ✅        | Path to YAML config file with insert data |
| INPUT_COMMIT_STRATEGY | ❌        | `per_table` or `all_or_nothing` (default) |

---

### Optional: SSH Tunnel Support

If your database is only reachable via a jump host (e.g. a private subnet), enable the SSH tunnel:

| Name                 | Required if tunneling | Description                                            |
|----------------------|-----------------------|--------------------------------------------------------|
| INPUT_USE_SSH_TUNNEL | ✅                     | Set to `"true"` to enable SSH tunneling                |
| INPUT_SSH_JUMP_HOST  | ✅                     | Hostname or IP of the jump/bastion server              |
| INPUT_SSH_JUMP_PORT  | ✅                     | SSH port for the jump server (default: 22)             |
| INPUT_SSH_JUMP_USER  | ✅                     | SSH user for the jump server                           |
| INPUT_SSH_JUMP_KEY   | ✅                     | Path to private SSH key (unencrypted or use ssh-agent) |
| INPUT_SSH_DB_HOST    | ✅                     | The internal hostname of the actual DB server          |
| INPUT_SSH_DB_PORT    | ✅                     | The DB port on the internal server (default: 3306)     |

---

## 🔧 YAML Configuration Format

Example `test-env-config.yaml`:

```yaml
tables:

- name: integration_settings
  entries:
    - id: "0x015cd7dd9afb452cb50d0b2289fec7ef"
      api_key: "test-api-key"
      webhook_url: "https://test.example.com/hook"

- name: system_config
  entries:
    - config_key: "mailer.transport"
      config_value: "smtp"
    - config_key: "mailer.host"
      config_value: "smtp.test.example.com"
```

### Notes:

- Binary values (e.g. BINARY(16) UUIDs) must be quoted hex: `"0x..."`
- You can insert multiple rows per table
- If `commit_strategy` is `per_table`, each table is committed independently
- If `all_or_nothing`, any failure aborts the whole transaction

---

## 🧪 Local Development

### Prerequisites

- Python 3.10+
- Docker (for running in GitHub Actions)
- MySQL database

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the script locally (direct DB)

```bash
export INPUT_DB_HOST=127.0.0.1  
export INPUT_DB_PORT=3306  
export INPUT_DB_NAME=test_db  
export INPUT_DB_USER=root  
export INPUT_DB_PASSWORD=secret  
export INPUT_CONFIG_FILE=test-env-config.yaml  
export INPUT_COMMIT_STRATEGY=all_or_nothing

python entrypoint.py
```

### Run with SSH tunnel (jump host access)

```bash
export USE_SSH_TUNNEL=true  
export SSH_JUMP_HOST=128.204.132.88  
export SSH_JUMP_PORT=22  
export SSH_JUMP_USER=ubuntu  
export SSH_JUMP_KEY=~/.ssh/id_rsa  
export SSH_DB_HOST=128.204.136.10  
export SSH_DB_PORT=3306

export INPUT_DB_NAME=test_db  
export INPUT_DB_USER=test_user  
export INPUT_DB_PASSWORD=test_pass  
export INPUT_CONFIG_FILE=test-env-config.yaml

python entrypoint.py
```

---

## 📁 Project Structure

```
.
├── action.yml # GitHub Action definition  
├── Dockerfile # Docker container for the action  
├── entrypoint.py # Main script logic  
├── requirements.txt # Python dependencies  
├── example-config.yaml # Example config file format  
└── README.md
```

---

## 🧭 Roadmap

- [ ] PostgreSQL support
- [ ] Pre- and post-insert SQL hooks
- [ ] YAML schema validation with type checks
- [ ] Dry-run mode (no DB writes, just validate and log)
- [ ] Support encrypted SSH keys

---

## 🤝 Contributing

Contributions welcome! Feel free to open an issue or PR for bugfixes, new database drivers, or feature enhancements.

---

## 🛡️ License

MIT — use freely, modify safely, and don’t leak your prod API keys.
