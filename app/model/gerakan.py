def serialize_gerakan(data):
    return {
        "id": str(data["_id"]),
        "nama_gerakan": data.get("nama_gerakan"),
        "gambar": data.get("gambar"),
        "instruksi": data.get("instruksi"),
        "repetisi": data.get("repetisi"),
        "durasi" : data.get("durasi")
    }
