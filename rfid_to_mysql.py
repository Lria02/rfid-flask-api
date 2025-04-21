from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure  # Updated import

# MongoDB connection details
MONGO_URI = "mongodb+srv://asunayuuki2435:Luxuria2024@cluster0.cba9vgk.mongodb.net/arduinoDB?retryWrites=true&w=majority"

app = Flask(__name__)

def connect_to_mongo():
    try:
        # Establishing connection to MongoDB
        client = MongoClient(MONGO_URI)
        db = client["arduinoDB"]  # This is the newly created database
        return db
    except ConnectionFailure as e:  # Handle connection failure
        print(f"❌ Error connecting to MongoDB: {e}")
        return None

@app.route('/scan', methods=['POST'])
def scan_rfid():
    # Get UID from the incoming request
    uid = request.json.get('uid')
    
    if not uid:
        return jsonify({"error": "No UID provided"}), 400

    # Connect to MongoDB
    db = connect_to_mongo()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    # Reference to the 'users' collection in the database
    collection = db["users"]

    try:
        # Check if UID already exists in the database
        user = collection.find_one({"rfid_UID": uid})

        if user:
            # UID already exists, print and return message
            print(f"✅ UID {uid} already exists in the database.")
        else:
            # If UID doesn't exist, insert it into the database
            collection.insert_one({"rfid_UID": uid, "total_recycled": 0, "coin": 0.00})
            print(f"🆕 New UID {uid} added to the database.")
        
        # Return success response
        return jsonify({"message": "UID processed successfully!"}), 200

    except Exception as e:
        # Handle any other exceptions
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask server on port 5000 and make it accessible on all IPs
    app.run(host='0.0.0.0', port=5000)
