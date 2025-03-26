# 📦 Post-Anonymization Secrets Populator

**Post-Anonymization Secrets Populator** is a GitHub Action that runs after a production database has been anonymized in a test environment. It safely inserts predefined secrets, plugin settings, and environment-specific configuration into your database to prevent test environments from pushing to real production APIs.

This tool reads a YAML configuration file that describes which rows to insert or update in specified database tables.

---

## 🚀 Use Case

When you copy production data to a test or staging environment, sensitive credentials (e.g., API keys, webhook URLs, SFTP settings) may still be present. This tool ensures test-safe replacements are inserted immediately after the anonymization step.

---

## 🧰 Features

- 🔐 Prevents accidental use of production integrations in test environments  
- ✅ Supports `INSERT ... ON DUPLICATE KEY UPDATE` for idempotency  
- ⚙️ Optional `commit_strategy`:
  - `per_table`: Commit each table independently (safer, partial success)
  - `all_or_nothing`: Fail entire action if any table fails (default, transactional)
- 🧠 Binary UUIDs supported via `"0x..."` auto-conversion
- 📄 YAML config for defining table entries
- 🐳 Docker-based GitHub Action  
- 💾 MySQL support (PostgreSQL planned)

---

## 🛠️ Usage in GitHub Actions

### Example Workflow

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
          db_name: ${{ secrets.DB_NAME }}
          db_user: ${{ secrets.DB_USER }}
          db_password: ${{ secrets.DB_PASSWORD }}
          config_file: test-env-config.yaml        # ✅ Required (lives in your project, check example-config.yaml for reference)
          commit_strategy: all_or_nothing          # optional: all_or_nothing (default) or per_table
```

---

## 🔐 Required Secrets / Inputs

| Name              | Required | Description                                |
|-------------------|----------|--------------------------------------------|
| `db_host`         | ✅       | Hostname of the MySQL database             |
| `db_name`         | ✅       | Database name                              |
| `db_user`         | ✅       | Database username                          |
| `db_password`     | ✅       | Database password                          |
| `config_file`     | ✅       | Path to YAML config file with insert data  |
| `commit_strategy` | ❌       | `per_table` or `all_or_nothing` (default)  |

---

## 🔧 YAML Configuration Format

Create a file like `test-env-config.yaml` in your repo root:

```yaml
tables:
  - name: your_table_name_here
    entries:
      - id: "0x015cd7dd9afb452cb50d0b2289fec7ef"  # ✅ must be quoted; auto-converted to BINARY(16)
        column2: value2
        column3: value3

      - column1: another_value1
        column2: another_value2
        column3: another_value3

  - name: another_table_name
    entries:
      - column1: yet_another_value1
        column2: yet_another_value2
        column3: yet_another_value3
```

### Notes:
- Field names must match your DB schema.
- Binary UUIDs should be written as quoted `"0x..."` hex strings.
- If `commit_strategy` is `per_table`, failed tables will be skipped with warnings.
- If `commit_strategy` is `all_or_nothing`, any error will abort the whole process.

---

## 🧪 Local Development

### Prerequisites

- Python 3.10+
- Docker (for running as an action)
- MySQL database

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the script locally

```bash
export INPUT_DB_HOST=localhost
export INPUT_DB_NAME=test_db
export INPUT_DB_USER=root
export INPUT_DB_PASSWORD=secret
export INPUT_CONFIG_FILE=test-env-config.yaml
export INPUT_COMMIT_STRATEGY=all_or_nothing  # or per_table
python entrypoint.py
```

---

## 📁 Project Structure

```
.
├── action.yml                  # GitHub Action definition
├── Dockerfile                  # Docker container for the action
├── entrypoint.py               # Main script logic
├── requirements.txt            # Python dependencies
├── example-config.yaml         # Example config file format
└── README.md
```

---

## 🧱 Roadmap

- [ ] PostgreSQL support  
- [ ] Pre- and post-insert SQL hooks  
- [ ] YAML schema validation with type checks  
- [ ] Dry-run mode (no DB writes, just validate and log)

---

## 🤝 Contributing

Contributions welcome! Feel free to open an issue or PR for bugfixes, new database drivers, or feature enhancements.

---

## 🛡️ License

MIT — use freely, modify safely, and don’t leak your prod API keys.
