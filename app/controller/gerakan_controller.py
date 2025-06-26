import os
import uuid
from flask import request, jsonify
from app import mongo
from bson.objectid import ObjectId
from app.model.gerakan import serialize_gerakan
from app.utils.admin_guard import require_admin_key

class GerakanController:

    @staticmethod
    @require_admin_key
    def create_gerakan():
        try:
            # Ambil data dari form
            nama_gerakan = request.form.get("nama_gerakan")
            instruksi = request.form.get("instruksi")
            repetisi = request.form.get("repetisi")

            # Validasi field wajib
            if not nama_gerakan or not instruksi:
                return jsonify({"success": False, "message": "Field 'nama_gerakan' dan 'instruksi' wajib diisi"}), 400

            # Proses file gambar
            file_gambar = request.files.get("gambar")
            filename_gambar = None
            if file_gambar:
                if file_gambar.filename == "":
                    return jsonify({"success": False, "message": "Nama file gambar kosong"}), 400
                ext = file_gambar.filename.rsplit('.', 1)[-1].lower()
                if ext not in {"jpg", "jpeg", "png", "gif"}:
                    return jsonify({"success": False, "message": "Format gambar tidak didukung"}), 400
                filename_gambar = f"{uuid.uuid4().hex}.{ext}"
                os.makedirs("upload/gerakan", exist_ok=True)
                file_gambar.save(os.path.join("upload/gerakan", filename_gambar))

            # Simpan ke database
            gerakan = {
                "nama_gerakan": nama_gerakan,
                "instruksi": instruksi,
                "repetisi": int(repetisi or 0),
                "gambar": f"/gambar/{filename_gambar}" if filename_gambar else None
            }

            result = mongo.db.gerakan.insert_one(gerakan)
            return jsonify({
                "success": True,
                "message": "Gerakan berhasil ditambahkan",
                "id": str(result.inserted_id),
                "gambar": gerakan["gambar"]
            })

        except Exception as e:
            return jsonify({"success": False, "message": f"Gagal menambahkan gerakan: {str(e)}"}), 500

    @staticmethod
    def get_all_gerakan():
        try:
            daftar = list(mongo.db.gerakan.find())
            serialized = [serialize_gerakan(g) for g in daftar]
            return jsonify({
                "success": True,
                "message": "Data gerakan berhasil diambil",
                "gerakan": serialized
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"Gagal mengambil gerakan: {str(e)}"}), 500
