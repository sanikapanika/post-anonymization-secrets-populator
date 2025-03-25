import os
import yaml
import mysql.connector
from mysql.connector import Error
import binascii

CONFIG_FILE = os.getenv("INPUT_CONFIG_FILE")

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
        "database": os.getenv("INPUT_DB_NAME"),
        "user": os.getenv("INPUT_DB_USER"),
        "password": os.getenv("INPUT_DB_PASSWORD"),
    }

    try:
        conn = mysql.connector.connect(**db_config)
        if not conn.is_connected():
            raise Exception("Database connection failed.")

        yaml_data = load_yaml(CONFIG_FILE)
        for table_data in yaml_data.get("tables", []):
            insert_entries(conn, table_data["name"], table_data["entries"])

        conn.commit()
        conn.close()
        print("Test environment secrets populated successfully.")

    except Error as e:
        print(f"MySQL error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
