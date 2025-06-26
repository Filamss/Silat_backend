from bson.objectid import ObjectId
from app import mongo

def serialize_latihan(data):
    return {
        "id": str(data["_id"]),
        "nama_latihan": data.get("nama_latihan"),
        "durasi": data.get("durasi"),
        "jumlah": data.get("jumlah"),
        "tanggal": data.get("tanggal"), 
        "gambar": data.get("gambar"),       
        "tingkat": data.get("tingkat"),
        "created_at": data.get("created_at"),
        "gerakan": data.get("gerakan", []) 
    }

def serialize_latihan_with_detail(data):
    latihan_serialized = {
        "id": str(data["_id"]),
        "nama_latihan": data.get("nama_latihan"),
        "durasi": data.get("durasi"),
        "jumlah": data.get("jumlah"),
        "tanggal": data.get("tanggal"),
        "gambar": data.get("gambar"),
        "tingkat": data.get("tingkat"),
        "created_at": data.get("created_at"),
        "gerakan": []
    }

    gerakan_refs = data.get("gerakan", [])
    for item in gerakan_refs:
        gerakan_id = item.get("gerakan_id")
        try:
            object_id = ObjectId(gerakan_id)
            detail = mongo.db.gerakan.find_one({"_id": object_id})
        except Exception:
            detail = None

        if detail:
            latihan_serialized["gerakan"].append({
            "gerakan_id": str(gerakan_id),
            "nama_gerakan": detail.get("nama_gerakan"),
            "instruksi": detail.get("instruksi"),
            "gambar": detail.get("gambar"),
            "durasi": detail.get("durasi"),
            "repetisi": detail.get("repetisi"),
            })
        else:
            latihan_serialized["gerakan"].append({
            "gerakan_id": str(gerakan_id),
            "nama_gerakan": detail.get("nama_gerakan"),
            "instruksi": detail.get("instruksi"),
            "gambar": detail.get("gambar"),
            "durasi": detail.get("durasi"),
            "repetisi": detail.get("repetisi"),
            })

    return latihan_serialized
