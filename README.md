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
- 📄 Simple YAML config for defining target tables and values  
- 🐳 Runs as a Docker-based GitHub Action  
- 💾 Supports MySQL databases (more to come)

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
          config_file: test-env-config.yaml
```

### Required Secrets

Define the following in your repository or organization:

- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

---

## 🔧 YAML Configuration Format

Create a file like `test-env-config.yaml` in your repo root:

```yaml
tables:
  - name: your_table_name_here
    entries:
      - id: "0x015cd7dd9afb452cb50d0b2289fec7ef" # Quotes must be there for binary values, script will parse the string to a binary, only it must begin with 0x
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
- Field names must match column names in your database.
- You can insert binary UUIDs using `"0x..."` notation — the tool will automatically convert them to raw `BINARY(16)` format.
- All inserts are idempotent via `ON DUPLICATE KEY UPDATE`.

---

## 🧪 Local Development

### Prerequisites

- Python 3.10+
- Docker (for GitHub Action testing)
- MySQL database (locally or remotely)

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

- [ ] Add PostgreSQL support  
- [ ] Support for truncating tables before insert  
- [ ] Support pre- and post-insert hooks  
- [ ] YAML schema validation with error messages

---

## 🤝 Contributing

Contributions welcome! Please open an issue or pull request if you'd like to improve functionality, add database drivers, or expand YAML support.

---

## 🛡️ License

MIT — do whatever you want, just don’t break production.
