from flask import request, jsonify
from app import mongo
from datetime import datetime

def simpan_riwayat_berat():
    data = request.get_json()
    email = data.get("email")
    berat = data.get("berat")

    if not email or berat is None:
        return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

    mongo.db.riwayat_berat.insert_one({
        "email": email,
        "berat": berat,
        "tanggal": datetime.utcnow()
    })

    return jsonify({"success": True, "message": "Berat badan berhasil disimpan"})

def ambil_riwayat_berat(email):
    data = list(mongo.db.riwayat_berat.find({"email": email}).sort("tanggal", -1))
    
    for item in data:
        item["_id"] = str(item["_id"])
        item["tanggal"] = item["tanggal"].isoformat()
    
    return jsonify({"success": True, "data": data})
