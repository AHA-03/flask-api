from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import qrcode
import base64
import uuid  # ✅ Import UUID for unique booking IDs
from io import BytesIO
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# ✅ Load Firebase Credentials from Environment Variable
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")

if firebase_json:
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
else:
    raise Exception("FIREBASE_SERVICE_ACCOUNT not found in environment variables")

# ✅ Initialize Firestore
db = firestore.client()

@app.route('/book_food', methods=['POST'])
def book_food():
    data = request.get_json()
    
    if not data or 'roll_number' not in data or 'phone_number' not in data or 'food_items' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    roll_number = data['roll_number']
    phone_number = data['phone_number']
    food_items = data['food_items']

    if not isinstance(food_items, list):
        return jsonify({"error": "Invalid food_items format"}), 400

    try:
        food_names = [item['food_item'] for item in food_items]
    except KeyError:
        return jsonify({"error": "Invalid food_items format"}), 400

    # ✅ Generate a unique Booking ID
    booking_id = str(uuid.uuid4())[:8]  # Shorter unique ID (first 8 chars)

    # ✅ Store in Firestore with Booking ID
    order_data = {
        "booking_id": booking_id,
        "roll_number": roll_number,
        "phone_number": phone_number,
        "food_items": food_items,
        "status": "pending"  # To track if food is dispensed
    }
    db.collection("orders").document(booking_id).set(order_data)

    # ✅ Generate QR Code with ONLY Booking ID
    qr = qrcode.make(booking_id)
    qr_io = BytesIO()
    qr.save(qr_io, format="PNG")
    qr_base64 = base64.b64encode(qr_io.getvalue()).decode('utf-8')

    return jsonify({"message": "Booking successful", "qr_code": qr_base64, "booking_id": booking_id})

@app.route('/get_order/<booking_id>', methods=['GET'])
def get_order(booking_id):
    # ✅ Fetch order details using Booking ID
    order_ref = db.collection("orders").document(booking_id).get()
    if order_ref.exists:
        return jsonify(order_ref.to_dict()), 200
    return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
