from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import qrcode
import base64
import uuid  # Import UUID for unique booking IDs
import os
import json
from io import BytesIO
from flask_cors import CORS

app = Flask(__name__)

# Restrict CORS to your frontend domain (modify as needed)
CORS(app, resources={r"/*": {"origins": "*"}})  # Change "*" to frontend URL if needed

# Load Firebase credentials from environment variable
firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS")
if firebase_credentials_json:
    cert = json.loads(firebase_credentials_json)
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    raise ValueError("FIREBASE_CREDENTIALS environment variable is missing.")

@app.route('/book_food', methods=['POST'])
def book_food():
    data = request.get_json()
    
    # Check if all required fields exist
    required_fields = {'roll_number', 'phone_number', 'food_items'}
    if not data or not required_fields.issubset(data):
        return jsonify({"error": "Missing required fields"}), 400

    roll_number = data['roll_number']
    phone_number = data['phone_number']
    food_items = data['food_items']

    # Validate `food_items` list
    if not isinstance(food_items, list) or not all(isinstance(item, dict) and 'food_item' in item for item in food_items):
        return jsonify({"error": "Invalid food_items format"}), 400

    food_names = [item['food_item'] for item in food_items]

    # Generate a unique Booking ID
    booking_id = str(uuid.uuid4())[:8]  # Shorter unique ID (first 8 chars)

    # Store in Firestore with Booking ID
    order_data = {
        "booking_id": booking_id,
        "roll_number": roll_number,
        "phone_number": phone_number,
        "food_items": food_names,  # Storing only food names for simplicity
        "status": "pending"  # To track if food is dispensed
    }
    db.collection("orders").document(booking_id).set(order_data)

    # Generate QR Code with ONLY Booking ID
    qr = qrcode.make(booking_id)
    qr_io = BytesIO()
    qr.save(qr_io, format="PNG")
    qr_base64 = base64.b64encode(qr_io.getvalue()).decode('utf-8')

    return jsonify({"message": "Booking successful", "qr_code": qr_base64, "booking_id": booking_id})

@app.route('/get_order/<booking_id>', methods=['GET'])
def get_order(booking_id):
    # Fetch order details using Booking ID
    order_ref = db.collection("orders").document(booking_id).get()
    if order_ref.exists:
        return jsonify(order_ref.to_dict()), 200
    return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)