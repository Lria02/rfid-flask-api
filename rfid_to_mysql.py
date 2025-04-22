from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# InfinityFree MySQL config
DB_CONFIG = {
    'host': 'sql100.infinityfree.com',
    'user': 'if0_38808215',
    'password': 'd2tN8zHet8GLsCy',
    'database': 'if0_38808215_dbarduino'
}

def connect_to_database():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Connected to InfinityFree MySQL database.")
            return connection
    except Error as e:
        print(f"❌ DB Connection Error: {e}")
        return None

@app.route('/scan', methods=['POST'])
def scan_rfid():
    try:
        data = request.get_json()
        uid = data.get('uid')

        if not uid or len(uid) < 4:
            return jsonify({'error': 'Invalid UID'}), 400

        db = connect_to_database()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE rfid_UID = %s", (uid,))
        result = cursor.fetchone()

        if result:
            response = {'message': '✅ UID already exists'}
        else:
            cursor.execute(
                "INSERT INTO users (rfid_UID, total_recycled, coin) VALUES (%s, 0, 0.00)",
                (uid,)
            )
            db.commit()
            response = {'message': f'🆕 UID {uid} registered'}

        cursor.close()
        db.close()
        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Render will override this port
