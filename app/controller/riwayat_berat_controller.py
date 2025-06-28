from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from datetime import datetime

@jwt_required()
def simpan_riwayat_berat():
    data = request.get_json()
    berat = data.get("berat")
    email = get_jwt_identity()

    if berat is None:
        return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

    mongo.db.riwayat_berat.insert_one({
        "email": email,
        "berat": berat,
        "tanggal": datetime.utcnow()
    })

    return jsonify({"success": True, "message": "Berat badan berhasil disimpan"})


@jwt_required()
def ambil_riwayat_berat():
    email = get_jwt_identity()
    data = list(mongo.db.riwayat_berat.find({"email": email}).sort("tanggal", -1))

    for item in data:
        item["_id"] = str(item["_id"])
        item["tanggal"] = item["tanggal"].isoformat()

    return jsonify({"success": True, "data": data})

