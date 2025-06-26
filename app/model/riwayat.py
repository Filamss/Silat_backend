from app import mongo
from bson.objectid import ObjectId
from datetime import datetime

def simpan_riwayat(user_id, durasi, kkal):
    riwayat = {
        "user_id": ObjectId(user_id),
        "tanggal": datetime.utcnow(),
        "durasi": durasi,
        "kkal": kkal,
    }
    result = mongo.db.riwayat.insert_one(riwayat)
    return str(result.inserted_id)

def get_riwayat_user(user_id):
    return list(mongo.db.riwayat.find({"user_id": ObjectId(user_id)}))
