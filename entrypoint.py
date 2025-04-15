import base64
import binascii
import os
import signal
import subprocess
import time

import mysql.connector
import yaml
from mysql.connector import Error

CONFIG_FILE = os.getenv("INPUT_CONFIG_FILE")


def write_ssh_key_from_base64(encoded_key: str, path: str) -> None:
    with open(path, "wb") as f:
        f.write(base64.b64decode(encoded_key))
    os.chmod(path, 0o600)


def get_commit_strategy():
    strategy = os.getenv("INPUT_COMMIT_STRATEGY", "all_or_nothing").lower()
    if strategy not in ["per_table", "all_or_nothing"]:
        print(f"Invalid commit strategy: {strategy}")
        exit(1)
    return strategy


def hex_to_bin(entry):
    for key, value in entry.items():
        if isinstance(value, str) and value.startswith("0x"):
            entry[key] = binascii.unhexlify(value[2:])  # Strip '0x' and convert to bytes
    return entry


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def insert_entries(conn, table, entries):
    cursor = conn.cursor()
    for entry in entries:
        entry = hex_to_bin(entry)
        columns = ", ".join(entry.keys())
        placeholders = ", ".join(["%s"] * len(entry))
        values = list(entry.values())

        updates = ", ".join([f"{col}=VALUES({col})" for col in entry.keys()])
        query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates};
        """
        cursor.execute(query, values)
    cursor.close()


def start_ssh_tunnel_if_enabled():
    if os.getenv("INPUT_USE_SSH_TUNNEL", "false").lower() != "true":
        return None, int(os.getenv("INPUT_DB_PORT", "3306"))

    local_port = 3307
    jump_host = os.getenv("INPUT_SSH_JUMP_HOST")
    jump_port = os.getenv("INPUT_SSH_JUMP_PORT", 22)
    db_host = os.getenv("INPUT_DB_HOST")
    db_port = os.getenv("INPUT_DB_PORT", "3306")
    ssh_user = os.getenv("INPUT_SSH_JUMP_USER")
    ssh_key_content = os.getenv("INPUT_SSH_JUMP_KEY")

    if not all([jump_host, db_host, ssh_user, ssh_key_content]):
        print("❌ SSH tunnel requested but missing environment variables.")
        exit(1)

    ssh_key_b64 = os.getenv("INPUT_SSH_JUMP_KEY")
    ssh_key_path = os.path.join(os.getcwd(), ".pasp_ssh_key")
    write_ssh_key_from_base64(ssh_key_b64, ssh_key_path)

    tunnel_cmd = [
        "ssh", "-f", "-N",
        "-L", f"{local_port}:{db_host}:{db_port}",
        f"{ssh_user}@{jump_host}",
        "-p", jump_port,
        "-i", ssh_key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ExitOnForwardFailure=yes"
    ]

    print(f"🚀 Starting SSH tunnel: localhost:{local_port} → {db_host}:{db_port} via {jump_host}")
    proc = subprocess.run(tunnel_cmd, check=True)
    time.sleep(2)
    return proc, local_port


def stop_ssh_tunnel(proc):
    if proc:
        print("🛑 Stopping SSH tunnel")
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except Exception as e:
            print(f"⚠️ Failed to kill SSH tunnel: {e}")


def main():
    proc, port = start_ssh_tunnel_if_enabled()

    db_config = {
        "host": "127.0.0.1" if proc else os.getenv("INPUT_DB_HOST"),
        "port": port,
        "database": os.getenv("INPUT_DB_NAME"),
        "user": os.getenv("INPUT_DB_USER"),
        "password": os.getenv("INPUT_DB_PASSWORD"),
    }

    try:
        conn = mysql.connector.connect(**db_config)
        if not conn.is_connected():
            raise Exception("Database connection failed.")

        strategy = get_commit_strategy()
        yaml_data = load_yaml(CONFIG_FILE)

        if strategy == "per_table":
            for table_data in yaml_data.get("tables", []):
                table_name = table_data["name"]
                entries = table_data["entries"]

                try:
                    print(f"Processing table: {table_name}")
                    insert_entries(conn, table_name, entries)
                    conn.commit()
                except Exception as e:
                    print(f"Skipped table '{table_name}' due to error: {e}")
                    conn.rollback()

        elif strategy == "all_or_nothing":
            try:
                print("Starting all-or-nothing transaction")
                for table_data in yaml_data.get("tables", []):
                    table_name = table_data["name"]
                    entries = table_data["entries"]

                    print(f"Processing table: {table_name}")
                    insert_entries(conn, table_name, entries)

                conn.commit()
                print("All changes committed.")
            except Exception as e:
                conn.rollback()
                print(f"❌ Transaction aborted due to error: {e}")
                exit(1)

        print("Test environment secrets populated successfully.")
    except Error as e:
        print(f"MySQL error: {e}")
        exit(1)
    finally:
        stop_ssh_tunnel(proc)


if __name__ == "__main__":
    main()
