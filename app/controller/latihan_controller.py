import os
import uuid
import json
from flask import jsonify, request
from app import mongo
from app.model.latihan import serialize_latihan
from app.model.latihan import serialize_latihan, serialize_latihan_with_detail
from datetime import datetime
from bson.objectid import ObjectId
from app.utils.admin_guard import require_admin_key

ALLOWED_GAMBAR = {"jpg", "jpeg", "png", "gif"}

def allowed_file(filename, jenis):
    ext = filename.rsplit('.', 1)[-1].lower()
    if jenis == "gambar":
        return ext in ALLOWED_GAMBAR
    return False

class LatihanController:

    @staticmethod
    def get_all_latihan():
        try:
            tingkat = request.args.get("tingkat")
            query = {"tingkat": tingkat} if tingkat else {}

            latihan_list = list(
                mongo.db.latihan
                .find(query)
                .sort("created_at", -1)
                .limit(50)
            )

            serialized = [serialize_latihan(item) for item in latihan_list]

            return jsonify({
                "success": True,
                "message": "Data latihan berhasil diambil",
                "latihan": serialized
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Gagal mengambil data latihan: {str(e)}"
            }), 500
    @staticmethod
    def get_latihan_by_id(id):
        try:
            latihan = mongo.db.latihan.find_one({"_id": ObjectId(id)})
            if not latihan:
                return jsonify({"success": False, "message": "Latihan tidak ditemukan"}), 404

            return jsonify({
                "success": True,
                "message": "Data latihan berhasil diambil",
                "latihan": serialize_latihan_with_detail(latihan)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Gagal mengambil data latihan: {str(e)}"
            }), 500


    @staticmethod
    def get_user_latihan_tanggal():
        try:
            latihan_list = list(mongo.db.latihan.find({}, {"created_at": 1}))

            tanggal_set = set()
            for item in latihan_list:
                if "created_at" in item:
                    tanggal = item["created_at"]
                    if isinstance(tanggal, datetime):
                        tanggal_set.add(tanggal.date().isoformat())

            return jsonify({
                "success": True,
                "message": "Tanggal latihan berhasil diambil",
                "tanggal_latihan": list(tanggal_set)
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Gagal mengambil tanggal latihan: {str(e)}"
            }), 500

    @staticmethod
    @require_admin_key
    def create_latihan():
        try:
            # Upload gambar
            file_gambar = request.files.get("gambar")
            filename_gambar = None
            if file_gambar and file_gambar.filename:
                ext = file_gambar.filename.rsplit('.', 1)[-1].lower()
                if ext not in ALLOWED_GAMBAR:
                    return jsonify({"success": False, "message": "Format gambar tidak didukung"}), 400
                filename_gambar = f"{uuid.uuid4().hex}.{ext}"
                os.makedirs("upload/gambar", exist_ok=True)
                file_gambar.save(os.path.join("upload/gambar", filename_gambar))

            # Ambil data form
            nama_latihan = request.form.get("nama_latihan")
            durasi = request.form.get("durasi")
            tingkat = request.form.get("tingkat")
            tanggal_str = request.form.get("tanggal")
            gerakan_json = request.form.get("gerakan")  # JSON array berisi nama_gerakan

            if not all([nama_latihan, durasi, tingkat, tanggal_str, gerakan_json]):
                return jsonify({"success": False, "message": "Semua field wajib diisi"}), 400

            try:
                durasi = int(durasi)
            except ValueError:
                return jsonify({"success": False, "message": "Durasi harus angka"}), 400

            try:
                datetime.strptime(tanggal_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"success": False, "message": "Format tanggal tidak valid"}), 400

            # Proses daftar nama_gerakan
            gerakan_names = json.loads(gerakan_json)
            if not isinstance(gerakan_names, list):
                return jsonify({"success": False, "message": "Gerakan harus berupa array"}), 400

            gerakan_ids = []
            for nama_gerakan in gerakan_names:
                data = mongo.db.gerakan.find_one({"nama_gerakan": nama_gerakan})
                if data:
                    gerakan_ids.append({"gerakan_id": str(data["_id"])})
                else:
                    return jsonify({"success": False, "message": f"Gerakan '{nama_gerakan}' tidak ditemukan"}), 400

            # Simpan ke MongoDB
            mongo.db.latihan.insert_one({
                "nama_latihan": nama_latihan,
                "durasi": durasi,
                "jumlah": len(gerakan_ids),
                "tingkat": tingkat.capitalize(),
                "tanggal": tanggal_str,
                "gambar": filename_gambar,
                "gerakan": gerakan_ids,
                "created_at": datetime.utcnow()
            })

            return jsonify({
                "success": True,
                "message": "Latihan berhasil ditambahkan"
            })

        except Exception as e:
            return jsonify({"success": False, "message": f"Terjadi kesalahan: {str(e)}"}), 500


    @staticmethod
    @require_admin_key
    def update_latihan(id):
        try:
            latihan = mongo.db.latihan.find_one({"_id": ObjectId(id)})
            if not latihan:
                return jsonify({"success": False, "message": "Latihan tidak ditemukan"}), 404

            # Data form
            nama_latihan = request.form.get("nama_latihan")
            durasi = request.form.get("durasi")
            tingkat = request.form.get("tingkat")
            tanggal = request.form.get("tanggal")
            gerakan_json = request.form.get("nama_gerakan")  
            if not all([nama_latihan, durasi, tingkat, tanggal, gerakan_json]):
                return jsonify({"success": False, "message": "Semua field wajib diisi"}), 400

            try:
                durasi = int(durasi)
            except ValueError:
                return jsonify({"success": False, "message": "Durasi harus angka"}), 400

            try:
                datetime.strptime(tanggal, "%Y-%m-%d")
            except ValueError:
                return jsonify({"success": False, "message": "Format tanggal tidak valid"}), 400

            # Ambil dan ubah gerakan berdasarkan nama
            gerakan_names = json.loads(gerakan_json)
            if not isinstance(gerakan_names, list):
                return jsonify({"success": False, "message": "Gerakan harus berupa array nama"}), 400

            gerakan_ids = []
            for nama_gerakan in gerakan_names:
                data = mongo.db.gerakan.find_one({"nama_gerakan": nama_gerakan})
                if data:
                    gerakan_ids.append({"gerakan_id": str(data["_id"])})
                else:
                    return jsonify({"success": False, "message": f"Gerakan '{nama_gerakan}' tidak ditemukan"}), 400

            # Optional: Update gambar jika dikirim
            file_gambar = request.files.get("gambar")
            filename_gambar = latihan.get("gambar")
            if file_gambar and file_gambar.filename:
                ext = file_gambar.filename.rsplit('.', 1)[-1].lower()
                if ext not in ALLOWED_GAMBAR:
                    return jsonify({"success": False, "message": "Format gambar tidak valid"}), 400
                filename_gambar = f"{uuid.uuid4().hex}.{ext}"
                os.makedirs("upload/gambar", exist_ok=True)
                file_gambar.save(os.path.join("upload/gambar", filename_gambar))

            # Update MongoDB
            mongo.db.latihan.update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "nama_latihan": nama_latihan,
                    "durasi": durasi,
                    "jumlah": len(gerakan_ids),
                    "tingkat": tingkat.capitalize(),
                    "tanggal": tanggal,
                    "gambar": filename_gambar,
                    "gerakan": gerakan_ids,
                    "updated_at": datetime.utcnow()
                }}
            )

            return jsonify({"success": True, "message": "Latihan berhasil diperbarui"})

        except Exception as e:
            return jsonify({"success": False, "message": f"Gagal update: {str(e)}"}), 500


    @staticmethod
    @require_admin_key
    def delete_latihan(id):
        try:
            query = {"_id": ObjectId(id)}
            result = mongo.db.latihan.delete_one(query)

            if result.deleted_count == 0:
                return jsonify({"success": False, "message": "Data tidak ditemukan"}), 404

            return jsonify({
                "success": True,
                "message": "Data latihan berhasil dihapus"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Gagal hapus latihan: {str(e)}"
            }), 500



