from flask import request, jsonify
from app.model import riwayat

def simpan_riwayat():
    data = request.json
    user_id = data.get("user_id")
    durasi = data.get("durasi")
    kkal = data.get("kkal")

    if not user_id or durasi is None or kkal is None:
        return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

    riwayat_id = riwayat.simpan_riwayat(user_id, durasi, kkal)
    return jsonify({"success": True, "message": "Riwayat disimpan", "id": riwayat_id})

def ambil_riwayat():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User ID diperlukan"}), 400

    data = riwayat.get_riwayat_user(user_id)
    return jsonify({"success": True, "data": data})
