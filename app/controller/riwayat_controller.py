from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.model import riwayat

@jwt_required()
def simpan_riwayat():
    data = request.json
    durasi = data.get("durasi")
    kkal = data.get("kkal")
    user_id = get_jwt_identity()

    if durasi is None or kkal is None:
        return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

    riwayat_id = riwayat.simpan_riwayat(user_id, durasi, kkal)
    return jsonify({"success": True, "message": "Riwayat disimpan", "id": riwayat_id})


@jwt_required()
def ambil_riwayat():
    user_id = get_jwt_identity()

    data = riwayat.get_riwayat_user(user_id)
    return jsonify({"success": True, "data": data})

