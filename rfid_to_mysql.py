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

@app.route('/')
def index():
    return "Hello, Flask is running!"

@app.route('/testdb', methods=['GET'])
def test_database_connection():
    """Test database connection independently."""
    try:
        print("🔍 Testing database connection...")
        db = connect_to_database()
        if db:
            print("✅ Database connection successful!")
            db.close()
            return jsonify({'message': 'Database connection successful'}), 200
        else:
            print("❌ Database connection failed.")
            return jsonify({'error': 'Database connection failed'}), 500
    except Exception as e:
        print(f"❌ Error during database test: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scan', methods=['POST'])
def scan_rfid():
    """Register a scanned RFID ID in the 'users' table or check if it already exists."""
    try:
        # Retrieve the JSON payload and extract the scanned UID
        data = request.get_json()
        uid = data.get("uid")
        if not uid:
            return jsonify({"error": "Missing 'uid' field in request"}), 400

        print(f"Processing scanned ID: {uid}")

        # Connect to the database
        connection = connect_to_database()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Check if the UID already exists in the 'users' table
        check_query = "SELECT * FROM users WHERE rfid_UID = %s"
        cursor.execute(check_query, (uid,))
        result = cursor.fetchone()

        if result:
            # UID already exists
            print(f"UID {uid} already exists in the database.")
            cursor.close()
            connection.close()
            return jsonify({"message": "existing"}), 200
        else:
            # Insert the new UID into the 'users' table
            insert_query = "INSERT INTO users (rfid_UID, total_recycled, coins) VALUES (%s, 0, 0.00)"
            cursor.execute(insert_query, (uid,))
            connection.commit()
            print(f"UID {uid} registered successfully.")
            cursor.close()
            connection.close()
            return jsonify({"message": "registered"}), 200

    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({"error": "An error occurred while processing the scan"}), 500

print("Registered URLs:")
print(app.url_map)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=10000, debug=True)
