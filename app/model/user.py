def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "nama": user["nama"],
        "email": user["email"],
        "otp_verified": user.get("otp_verified", False),
        "profile_complete": user.get("profile_complete", False),  
        "umur": user.get("umur"),
        "tinggi": user.get("tinggi"),
        "berat": user.get("berat")
    }
