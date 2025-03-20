import os
import base64
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyqrcode
import razorpay
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Debugging: Print Environment Variable
firebase_base64 = os.getenv("FIREBASE_CONFIG_BASE64")

if not firebase_base64:
    raise ValueError("❌ ERROR: FIREBASE_CONFIG_BASE64 is not set. Please check your environment variables.")

try:
    firebase_json = base64.b64decode(firebase_base64).decode()
    print("✅ Decoded Firebase JSON Successfully!")
    firebase_config = json.loads(firebase_json)

    # Write Firebase credentials to a temporary JSON file
    with open("firebase_config.json", "w") as f:
        json.dump(firebase_config, f)

    # Initialize Firebase Admin SDK
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized successfully!")

except Exception as e:
    raise ValueError(f"❌ Error in Firebase setup: {e}")

# Razorpay Configuration
razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY"), os.getenv("RAZORPAY_SECRET")))

@app.route("/")
def home():
    return jsonify({"message": "Food Dispenser API is running!"})

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json
        booking_id = data.get("booking_id")

        if not booking_id:
            return jsonify({"error": "Missing booking_id"}), 400

        qr = pyqrcode.create(booking_id)
        buffer = BytesIO()
        qr.png(buffer, scale=6)
        buffer.seek(0)

        return buffer.getvalue(), 200, {"Content-Type": "image/png"}
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create_order", methods=["POST"])
def create_order():
    try:
        data = request.json
        amount = data.get("amount")

        if not amount:
            return jsonify({"error": "Amount is required"}), 400

        order = razorpay_client.order.create({
            "amount": int(amount) * 100,  # Convert to paise
            "currency": "INR",
            "payment_capture": 1
        })

        return jsonify(order)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/verify_payment", methods=["POST"])
def verify_payment():
    try:
        data = request.json
        order_id = data.get("order_id")
        payment_id = data.get("payment_id")
        signature = data.get("signature")

        if not (order_id and payment_id and signature):
            return jsonify({"error": "Missing payment details"}), 400

        params_dict = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            return jsonify({"message": "Payment verified successfully"}), 200
        except:
            return jsonify({"error": "Invalid payment signature"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
