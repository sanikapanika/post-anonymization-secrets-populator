import os
import yaml
import mysql.connector
from mysql.connector import Error
import binascii

CONFIG_FILE = os.getenv("INPUT_CONFIG_FILE")

def get_commit_strategy():
    strategy = os.getenv("INPUT_COMMIT_STRATEGY", "all_or_nothing").lower()
    if strategy not in ["per_table", "all_or_nothing"]:
        print(f"❌ Invalid commit strategy: {strategy}")
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
        entry = hex_to_bin(entry) # Convert hex strings to binary if necessary
        columns = ", ".join(entry.keys())
        placeholders = ", ".join(["%s"] * len(entry))
        values = list(entry.values())

        # Use INSERT ... ON DUPLICATE KEY UPDATE to avoid duplication
        updates = ", ".join([f"{col}=VALUES({col})" for col in entry.keys()])

        query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates};
        """

        cursor.execute(query, values)
    cursor.close()

def main():
    db_config = {
        "host": os.getenv("INPUT_DB_HOST"),
        "port": os.getenv("INPUT_DB_PORT"),
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
                print("✅ All changes committed.")
            except Exception as e:
                conn.rollback()
                print(f"❌ Transaction aborted due to error: {e}")
                exit(1)

        print("Test environment secrets populated successfully.")
    except Error as e:
        print(f"MySQL error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
