from flask import request
from bson import ObjectId
from app import mongo, response
from app.model.artikel import serialize_artikel
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'upload'

def create_artikel():
    judul = request.form.get("judul")
    konten = request.form.get("konten")
    penulis = request.form.get("penulis")
    file = request.files.get("foto")

    if not judul or not konten or not penulis or not file:
        return response.error([], "Semua field wajib diisi termasuk foto")

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    mongo.db.silat_artikel.insert_one({
        "judul": judul,
        "konten": konten,
        "penulis": penulis,
        "foto": filename
    })

    return response.success({}, "Artikel berhasil dibuat")

def get_artikel():
    artikels = mongo.db.silat_artikel.find()
    result = [serialize_artikel(a) for a in artikels]
    return response.success(result, "Daftar artikel")

def get_artikel_by_id(id):
    artikel = mongo.db.silat_artikel.find_one({"_id": ObjectId(id)})
    if not artikel:
        return response.error([], "Artikel tidak ditemukan")
    return response.success(serialize_artikel(artikel), "Detail artikel")

def update_artikel(id):
    artikel = mongo.db.silat_artikel.find_one({"_id": ObjectId(id)})
    if not artikel:
        return response.error([], "Artikel tidak ditemukan")

    judul = request.form.get("judul")
    konten = request.form.get("konten")
    penulis = request.form.get("penulis")
    file = request.files.get("foto")

    update_data = {
        "judul": judul or artikel["judul"],
        "konten": konten or artikel["konten"],
        "penulis": penulis or artikel["penulis"]
    }

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        update_data["foto"] = filename

    mongo.db.silat_artikel.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    return response.success({}, "Artikel berhasil diperbarui")

def delete_artikel(id):
    deleted = mongo.db.silat_artikel.delete_one({"_id": ObjectId(id)})
    if deleted.deleted_count == 0:
        return response.error([], "Artikel tidak ditemukan")
    return response.success({}, "Artikel berhasil dihapus")
