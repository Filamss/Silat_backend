import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client.silatdb
otp_collection = db.otp_collection

# Simpan OTP dengan waktu kedaluwarsa 2 menit
def store_otp_in_db(email, otp):
    otp_collection.update_one(
        {"email": email},
        {
            "$set": {
                "otp": otp,
                "expires_at": datetime.utcnow() + timedelta(minutes=2)
            }
        },
        upsert=True
    )

# Ambil OTP hanya jika belum kadaluarsa
def get_otp_from_db(email):
    now = datetime.utcnow()
    return otp_collection.find_one({
        "email": email,
        "expires_at": {"$gt": now}
    })
