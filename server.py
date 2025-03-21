from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import qrcode
import base64
import uuid
from io import BytesIO
from flask_cors import CORS
import razorpay

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# 🔑 Replace with your Razorpay API Keys
RAZORPAY_KEY_ID = "rzp_test_grC8eQKnPL68OR"
RAZORPAY_KEY_SECRET = "arHvtjlLsJOGxxcMYnpgejfJ"

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# 🔥 Firebase Admin SDK
cred = credentials.Certificate(r"F:\AA01FOOD DISPENSER\serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ Create Razorpay Order
@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        data = request.json
        total_amount = data.get("amount")  # Amount in INR

        if not total_amount:
            return jsonify({"error": "Amount is required"}), 400

        # Create order in Razorpay
        order = razorpay_client.order.create({
            "amount": int(total_amount) * 100,  # Convert to paise
            "currency": "INR",
            "payment_capture": 1  # Auto-capture payment
        })

        return jsonify({"order_id": order["id"], "amount": order["amount"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Verify Payment and Generate QR Code
@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    try:
        data = request.json
        payment_id = data.get("razorpay_payment_id")
        order_id = data.get("razorpay_order_id")
        signature = data.get("razorpay_signature")
        roll_number = data.get("roll_number")
        phone_number = data.get("phone_number")
        food_items = data.get("food_items")

        if not all([payment_id, order_id, signature, roll_number, phone_number, food_items]):
            return jsonify({"error": "Missing required fields"}), 400

        # Verify Razorpay Signature
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })

        # Generate unique Booking ID
        booking_id = str(uuid.uuid4())[:8]
        order_data = {
            "booking_id": booking_id,
            "roll_number": roll_number,
            "phone_number": phone_number,
            "food_items": food_items,
            "status": "confirmed"
        }
        db.collection("orders").document(booking_id).set(order_data)

        # Generate QR Code for Booking ID
        qr = qrcode.make(booking_id)
        qr_io = BytesIO()
        qr.save(qr_io, format="PNG")
        qr_base64 = base64.b64encode(qr_io.getvalue()).decode('utf-8')

        return jsonify({"message": "Payment verified", "qr_code": qr_base64, "booking_id": booking_id}), 200

    except Exception as e:
        return jsonify({"error": "Payment verification failed: " + str(e)}), 400


# 🔥 Run Flask Server
if __name__ == '__main__':
    app.run(debug=True)
