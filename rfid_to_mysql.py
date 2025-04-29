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

@app.route('/sensor', methods=['POST'])
def process_sensor_data():
    """Handle bottle detection and signal RFID scan request."""
    try:
        # Retrieve the JSON payload
        data = request.get_json()
        bottle_detected = data.get("bottle_detected")
        if bottle_detected is None:
            return jsonify({"error": "Missing 'bottle_detected' field in request"}), 400
        
        print("Bottle detected, ready for RFID scan.")

        # Notify the ESP32 to start the scan
        # This can be expanded later to handle more logic based on the sensor data
        return jsonify({"message": "Bottle detected, waiting for RFID scan"}), 200

    except Exception as e:
        print(f"Error during bottle detection: {e}")
        return jsonify({"error": "An error occurred while processing the sensor data"}), 500

@app.route('/redeem', methods=['POST'])
def redeem_coins():
    """Handle coin redemption for a given UID."""
    try:
        # Retrieve the JSON payload and extract the UID
        data = request.get_json()
        uid = data.get("uid")
        if not uid:
            return jsonify({"error": "Missing 'uid' field in request"}), 400

        print(f"Processing redemption for UID: {uid}")

        # Connect to the database
        connection = connect_to_database()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Check the current coin balance for the UID
        check_query = "SELECT coins FROM users WHERE rfid_UID = %s"
        cursor.execute(check_query, (uid,))
        result = cursor.fetchone()

        if not result:
            # UID not found
            print(f"UID {uid} not found in the database.")
            cursor.close()
            connection.close()
            return jsonify({"error": "UID not found"}), 404

        # Calculate the number of whole coins that can be redeemed
        current_coins = float(result[0])
        redeemable_coins = int(current_coins)  # Whole number of coins

        if redeemable_coins == 0:
            print(f"UID {uid} has no redeemable coins.")
            cursor.close()
            connection.close()
            return jsonify({"message": "No coins to redeem", "coins": 0}), 200

        # Update the database: Deduct redeemed coins
        updated_coins = current_coins - redeemable_coins
        update_query = "UPDATE users SET coins = %s WHERE rfid_UID = %s"
        cursor.execute(update_query, (updated_coins, uid))
        connection.commit()

        print(f"Redeemed {redeemable_coins} coins for UID {uid}. New balance: {updated_coins}")
        cursor.close()
        connection.close()

        # Return the number of coins to dispense
        return jsonify({"message": "Coins redeemed", "coins": redeemable_coins}), 200

    except Exception as e:
        print(f"Error during coin redemption: {e}")
        return jsonify({"error": "An error occurred during coin redemption"}), 500


print("Registered URLs:")
print(app.url_map)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=10000, debug=True)
