from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import qrcode
import io
import base64
import razorpay
from flask_cors import CORS
from flask import Flask, jsonify



# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Firebase
cred = credentials.Certificate("F:\ZZZ\serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
app = Flask(__name__)

@app.route("/test_firebase", methods=["GET"])
def test_firebase():
    try:
        # Try fetching a document (or just ping Firestore)
        test_ref = db.collection("test").document("connection").get()
        if test_ref.exists:
            return jsonify({"status": "connected", "message": "Firebase is working!"})
        else:
            return jsonify({"status": "connected", "message": "Connected, but no test data found."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=("rzp_test_grC8eQKnPL68OR", "arHvtjlLsJOGxxcMYnpgejfJ"))

# Booking API - Handles food orders & payment verification
@app.route("/book_food", methods=["POST"])
def book_food():
    data = request.json
    phone_number = data["phone_number"]
    food_items = data["food_items"]
    payment_id = data["payment_id"]

    # Verify payment with Razorpay
    try:
        payment = razorpay_client.payment.fetch(payment_id)
        if payment["status"] != "captured":
            return jsonify({"status": "error", "message": "Payment not successful"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    # Store booking in Firestore
    booking_ref = db.collection("bookings").add({
        "phone_number": phone_number,
        "food_items": food_items,
        "payment_id": payment_id
    })
    booking_id = booking_ref[1].id

    # Generate QR Code
    qr_data = {"booking_id": booking_id, "phone_number": phone_number}
    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({"qr_code": qr_base64})

# QR Verification API - ESP32 sends scanned QR code, backend verifies
@app.route("/verify_qr", methods=["POST"])
def verify_qr():
    data = request.json
    scanned_qr = data["scanned_qr"]

    try:
        qr_decoded = base64.b64decode(scanned_qr).decode()
        booking_id = qr_decoded["booking_id"]
        booking_ref = db.collection("bookings").document(booking_id).get()
        
        if not booking_ref.exists:
            return jsonify({"status": "rejected", "message": "Invalid QR code"})
        
        booking_data = booking_ref.to_dict()
        return jsonify({"status": "approved", "food_items": booking_data["food_items"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)





app = Flask(__name__)

@app.route("/test_firebase", methods=["GET"])
def test_firebase():
    try:
        # Try fetching a document (or just ping Firestore)
        test_ref = db.collection("test").document("connection").get()
        if test_ref.exists:
            return jsonify({"status": "connected", "message": "Firebase is working!"})
        else:
            return jsonify({"status": "connected", "message": "Connected, but no test data found."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
