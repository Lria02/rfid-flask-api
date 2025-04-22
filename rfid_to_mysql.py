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
    """Receive scanned RFID UID and register it in the database if it does not already exist."""
    try:
        # Parse the JSON payload for the UID
        data = request.get_json()
        uid = data.get("uid")
        if not uid:
            return jsonify({'error': "Missing 'uid' field in request"}), 400
        
        # Connect to the database
        db = connect_to_database()
        if not db:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = db.cursor()
        
        # Check if the UID already exists in the 'rfid_scans' table
        select_query = "SELECT COUNT(*) FROM rfid_scans WHERE uid = %s"
        cursor.execute(select_query, (uid,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # UID already exists in the database
            message = 'existing'
        else:
            # Insert the new UID into the database
            insert_query = "INSERT INTO rfid_scans (uid) VALUES (%s)"
            cursor.execute(insert_query, (uid,))
            db.commit()
            message = 'registered'
        
        cursor.close()
        db.close()
        
        print(f"Processed UID: {uid} -> {message}")
        return jsonify({'message': message}), 200

    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=10000, debug=True)
