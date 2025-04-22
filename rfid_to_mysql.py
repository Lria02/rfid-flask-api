import serial
import mysql.connector
from mysql.connector import Error
import time

# Serial config
SERIAL_PORT = 'COM5'  # Change this!
BAUD_RATE = 9600

# InfinityFree MySQL config
DB_CONFIG = {
    'host': 'sql100.infinityfree.com',        # Replace with your actual DB host
    'user': 'if0_38808215',           # Replace with your InfinityFree DB user
    'password': 'd2tN8zHet8GLsCy',  # Replace with your InfinityFree DB password
    'database': 'if0_38808215_dbarduino' # Replace with your DB name
}

def connect_to_database():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Connected to InfinityFree MySQL database.")
            return connection
    except Error as e:
        print(f"❌ Error: {e}")
        return None

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"📡 Listening on {SERIAL_PORT} at {BAUD_RATE} baud...")
        time.sleep(2)
    except Exception as e:
        print(f"❌ Serial error: {e}")
        return

    db = connect_to_database()
    if not db:
        return

    cursor = db.cursor()

    try:
        while True:
            uid = ser.readline().decode().strip()

            if not uid or "Scan" in uid:
                continue

            print(f"📨 UID Received: {uid}")
            
            cursor.execute("SELECT * FROM users WHERE rfid_UID = %s", (uid,))
            result = cursor.fetchone()

            if result:
                print("✅ UID already exists in database.")
            else:
                cursor.execute(
                    "INSERT INTO users (rfid_UID, total_recycled, coin) VALUES (%s, 0, 0.00)",
                    (uid,)
                )
                db.commit()
                print(f"🆕 New UID added to database: {uid}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    finally:
        ser.close()
        cursor.close()
        db.close()

if __name__ == '__main__':
    main()
