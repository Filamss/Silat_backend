def serialize_artikel(data):
    return {
        "id": str(data["_id"]),
        "judul": data["judul"],
        "konten": data["konten"],
        "penulis": data["penulis"],
        "foto": data.get("foto", "")
    }
