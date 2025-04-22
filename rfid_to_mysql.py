from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Aiven MySQL configuration
DB_CONFIG = {
    'host': 'mysql-a920a0-tanginarduino.k.aivencloud.com',
    'user': 'avnadmin',
    'password': 'AVNS_NW5T9_kZefmCceB6eA2',
    'database': 'defaultdb',
    'port': 28795,
    'ssl_ca': './ca.pem'  # Path to the CA certificate
}

def connect_to_database():
    """Establish a secure connection to the MySQL database."""
    try:
        print(f"Connecting to database at {DB_CONFIG['host']} on port {DB_CONFIG['port']}")
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Database connection successful!")
            return connection
    except Error as e:
        print(f"Database connection error: {e}")
    return None

@app.route('/scan', methods=['POST'])
def scan_rfid():
    """Register a scanned RFID ID in the database."""
    try:
        # Retrieve the JSON payload and extract the scanned UID
        data = request.get_json()
        uid = data.get("uid")
        if not uid:
            return jsonify({"error": "Missing 'uid' field in request body"}), 400

        print(f"Registering scanned ID: {uid}")

        # Connect to the database
        connection = connect_to_database()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Insert the scanned ID into the 'rfid_scans' table.
        # Ensure that your MySQL database has a table named 'rfid_scans' with at least one column 'uid'.
        query = "INSERT INTO rfid_scans (uid) VALUES (%s)"
        cursor.execute(query, (uid,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"message": "Scanned ID registered successfully"}), 200

    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({"error": "An error occurred while processing the scan"}), 500

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=10000, debug=True)
