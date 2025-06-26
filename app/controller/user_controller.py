import random
import uuid
import smtplib
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import mongo, response
from app.api_service import generate_token
from app.model.user import serialize_user
from email.mime.text import MIMEText
from config import MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER, MAIL_USERNAME
from database import get_otp_from_db, store_otp_in_db
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = "1082666813493-b45d6ti72k5cvahp6hnno4c18nq1o2t5.apps.googleusercontent.com"

class UserController:

    @staticmethod
    def register():
        data = request.get_json()
        nama = data.get("nama")
        email = data.get("email")
        password = data.get("password")

        if not nama or not email or not password:
            return response.error([], "Semua field wajib diisi")

        if mongo.db.user.find_one({"email": email}):
            return response.error([], "Email sudah terdaftar")

        hashed_pw = generate_password_hash(password)
        mongo.db.user.insert_one({
            "nama": nama,
            "email": email,
            "password": hashed_pw,
            "otp_verified": False,
            "jenis_kelamin": None,
            "profile_complete": False
        })

        otp = UserController.generate_otp()
        store_otp_in_db(email, otp)

        if UserController.send_otp_email(email, otp):
            user = mongo.db.user.find_one({"email": email})
            return response.success({
                "user": serialize_user(user),
                "otp": otp
            }, "Registrasi berhasil. OTP telah dikirim ke email.")
        else:
            return response.error([], "Gagal mengirim OTP ke email.")

    @staticmethod
    def login():
        data = request.json
        email = data.get("email")
        password = data.get("password")

        user = mongo.db.user.find_one({"email": email})
        if not user or not check_password_hash(user["password"], password):
            return response.error([], "Email atau password salah")

        if not user.get("otp_verified", False):
            return response.error([], "Akun belum diverifikasi melalui OTP")

        token = generate_token(str(user["_id"]))
        return response.success({
            "token": token,
            "user": serialize_user(user)
        }, "Login berhasil")


    @staticmethod
    def login_google():
        data = request.get_json()
        id_token_str = data.get("idToken")
        if not id_token_str:
            return response.error([], "Token tidak ditemukan")

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
            email = idinfo["email"]
            nama = idinfo.get("name", "Pengguna Google")

            user = mongo.db.user.find_one({"email": email})
            if not user:
                mongo.db.user.insert_one({
                    "nama": nama,
                    "email": email,
                    "password": None,
                    "otp_verified": True,
                    "jenis_kelamin": None,
                    "profile_complete": False
                })
                user = mongo.db.user.find_one({"email": email})

            return response.success({
                "user": serialize_user(user)
            }, "Login Google berhasil")

        except Exception as e:
            return response.error([], f"Token tidak valid: {str(e)}")

    @staticmethod
    def verify_otp():
        data = request.get_json()
        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            return response.error([], "Email dan OTP wajib diisi")

        stored_otp = get_otp_from_db(email)
        if stored_otp and stored_otp["otp"] == otp:
            mongo.db.user.update_one({"email": email}, {"$set": {"otp_verified": True}})
            user = mongo.db.user.find_one({"email": email})
            return response.success({
                "user": serialize_user(user)
            }, "OTP berhasil diverifikasi.")
        else:
            return response.error([], "OTP tidak valid.")

    @staticmethod
    def resend_otp():
        data = request.get_json()
        email = data.get("email")

        if not email:
            return response.error([], "Email wajib diisi")

        user = mongo.db.user.find_one({"email": email})
        if not user:
            return response.error([], "Email tidak ditemukan")

        if user.get("otp_verified", False):
            return response.error([], "Akun sudah diverifikasi, tidak perlu kirim ulang OTP")

        otp = UserController.generate_otp()
        store_otp_in_db(email, otp)

        if UserController.send_otp_email(email, otp):
            return response.success({"otp": otp}, "OTP berhasil dikirim ulang")
        else:
            return response.error([], "Gagal mengirim ulang OTP")

    @staticmethod
    def generate_otp():
        return str(random.randint(1000, 9999))

    @staticmethod
    def send_otp_email(email, otp):
        body = f"Kode OTP Anda adalah {otp}. Gunakan untuk verifikasi."
        msg = MIMEText(body)
        msg["Subject"] = "Kode OTP Anda"
        msg["From"] = MAIL_USERNAME
        msg["To"] = email

        try:
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
                server.starttls()
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception:
            return False
        
    @staticmethod
    def is_profile_complete(user):
        required_fields = ['jenis_kelamin', 'umur', 'tinggi', 'berat']
        return all(user.get(field) not in (None, "") for field in required_fields)

    @staticmethod
    def update_profile_status(email):
        user = mongo.db.user.find_one({"email": email})
        if user:
            complete = UserController.is_profile_complete(user)
            mongo.db.user.update_one(
                {"email": email},
                {"$set": {"profile_complete": complete}}
            )

    @staticmethod
    def update_jenis_kelamin():
        data = request.get_json()
        email = data.get("email")
        jenis_kelamin = data.get("jenis_kelamin")

        if not email or not jenis_kelamin:
            return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

        result = mongo.db.user.update_one(
            {"email": email},
            {"$set": {"jenis_kelamin": jenis_kelamin}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Pengguna tidak ditemukan"}), 404

        UserController.update_profile_status(email)

        return jsonify({"success": True, "message": "Jenis kelamin berhasil diperbarui"})

    
    @staticmethod
    def update_umur():
        data = request.get_json()
        email = data.get("email")
        umur = data.get("umur")

        if not email or umur is None:
            return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

        result = mongo.db.user.update_one(
            {"email": email},
            {"$set": {"umur": umur}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Pengguna tidak ditemukan"}), 404

        UserController.update_profile_status(email)

        return jsonify({"success": True, "message": "Umur berhasil diperbarui"})

    @staticmethod
    def update_tinggi():
        data = request.get_json()
        email = data.get("email")
        tinggi = data.get("tinggi")

        if not email or tinggi is None:
            return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

        result = mongo.db.user.update_one(
            {"email": email},
            {"$set": {"tinggi": tinggi}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Pengguna tidak ditemukan"}), 404

        UserController.update_profile_status(email)

        return jsonify({"success": True, "message": "Tinggi badan berhasil diperbarui"})

    @staticmethod
    def update_berat():
        data = request.get_json()
        email = data.get("email")
        berat = data.get("berat")

        if not email or berat is None:
            return jsonify({"success": False, "message": "Data tidak lengkap"}), 400

        result = mongo.db.user.update_one(
            {"email": email},
            {"$set": {"berat": berat}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Pengguna tidak ditemukan"}), 404

        UserController.update_profile_status(email)

        return jsonify({"success": True, "message": "Berat badan berhasil diperbarui"})
    
    @staticmethod
    def logout():
        # Karena JWT disimpan di klien, cukup beri pesan bahwa token harus dihapus di sisi klien
        return response.success({}, "Berhasil logout.")

    

    
    
