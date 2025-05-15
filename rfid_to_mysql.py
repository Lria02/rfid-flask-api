from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

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
    """Register or check an RFID UID."""
    try:
        data = request.get_json()
        uid = data.get("uid")
        if not uid:
            return jsonify({"error": "Missing 'uid' field in request"}), 400

        print(f"Processing scanned ID: {uid}")
        connection = connect_to_database()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Check if UID exists
        check_query = "SELECT * FROM users WHERE rfid_UID = %s"
        cursor.execute(check_query, (uid,))
        result = cursor.fetchone()

        if result:
            print(f"UID {uid} exists in the database.")
            cursor.close()
            connection.close()
            return jsonify({"message": "existing"}), 200
        else:
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
def handle_bottle_with_uid():
    """Handle bottle recycling and increment coins."""
    data = request.get_json()
    uid = data.get("uid")

    if not uid:
        return jsonify({"error": "UID missing"}), 400

    connection = connect_to_database()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor()

    # Check if UID exists
    cursor.execute("SELECT coins FROM users WHERE rfid_UID = %s", (uid,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        connection.close()
        return jsonify({"error": "UID not registered"}), 404

    current_coins = float(result[0])
    new_coins = current_coins + 5

    cursor.execute("UPDATE users SET coins = %s WHERE rfid_UID = %s", (new_coins, uid))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"status": "recycled", "coins": new_coins}), 200

@app.route('/redeem', methods=['POST'])
def redeem_coins():
    """Handle coin redemption."""
    try:
        data = request.get_json()
        uid = data.get("uid")
        if not uid:
            return jsonify({"error": "Missing 'uid' field in request"}), 400

        print(f"Processing redemption for UID: {uid}")
        connection = connect_to_database()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Check coin balance
        check_query = "SELECT coins FROM users WHERE rfid_UID = %s"
        cursor.execute(check_query, (uid,))
        result = cursor.fetchone()

        if not result:
            print(f"UID {uid} not found in database.")
            cursor.close()
            connection.close()
            return jsonify({"error": "UID not found"}), 404

        current_coins = float(result[0])
        redeemable_coins = int(current_coins)

        if redeemable_coins == 0:
            print(f"UID {uid} has no coins to redeem.")
            cursor.close()
            connection.close()
            return jsonify({"message": "No coins to redeem", "coins": 0}), 200

        updated_coins = current_coins - redeemable_coins
        update_query = "UPDATE users SET coins = %s WHERE rfid_UID = %s"
        cursor.execute(update_query, (updated_coins, uid))
        connection.commit()

        print(f"Redeemed {redeemable_coins} coins for UID {uid}. New balance: {updated_coins}")
        cursor.close()
        connection.close()

        return jsonify({"message": "Coins redeemed", "coins": redeemable_coins}), 200

    except Exception as e:
        print(f"Error during coin redemption: {e}")
        return jsonify({"error": "An error occurred during coin redemption"}), 500

print("Registered URLs:")
print(app.url_map)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=10000, debug=True)
