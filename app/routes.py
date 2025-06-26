from functools import wraps
from app.controller.user_controller import UserController
from app.controller.latihan_controller import LatihanController
from app.controller.gerakan_controller import GerakanController
from app.controller import riwayat_controller
from app.controller import artikel_controller
from app.controller import riwayat_berat_controller
from app.model.gerakan import serialize_gerakan
from app.model.latihan import serialize_latihan_with_detail
from app.utils.api_key_guard import require_api_key
from flask import jsonify, render_template, request, redirect, session, url_for
from app import mongo, bcrypt
from bson.objectid import ObjectId
from datetime import datetime
import os
import uuid

def init_routes(app):
    # ===================== #
    # 🔐 API ENDPOINT (For FLUTTER)
    # ===================== #
    app.route('/api/register', methods=['POST'])(UserController.register)
    app.route('/api/login', methods=['POST'])(UserController.login)
    app.route("/api/login-google", methods=["POST"])(UserController.login_google)
    app.route('/api/logout', methods=['POST'])(UserController.logout)
    app.route("/api/verify-otp", methods=["POST"])(UserController.verify_otp)
    app.route('/api/resend-otp', methods=['POST'])(UserController.resend_otp)
    app.route("/api/update-jenis-kelamin", methods=["POST"])(UserController.update_jenis_kelamin)
    app.route('/api/update-umur', methods=['POST'])(UserController.update_umur)
    app.route('/api/update-tinggi', methods=['POST'])(UserController.update_tinggi)
    app.route('/api/update-berat', methods=['POST'])(UserController.update_berat)

    app.route('/api/artikel', methods=['POST'])(artikel_controller.create_artikel)
    app.route('/api/artikel', methods=['GET'])(artikel_controller.get_artikel)
    app.route('/api/artikel/<id>', methods=['GET'])(artikel_controller.get_artikel_by_id)
    app.route('/api/artikel/<id>', methods=['PUT'])(artikel_controller.update_artikel)
    app.route('/api/artikel/<id>', methods=['DELETE'])(artikel_controller.delete_artikel)

    app.route("/api/latihan", methods=["GET"])(LatihanController.get_all_latihan)
    app.route("/api/latihan", methods=["POST"])(LatihanController.create_latihan)
    app.route("/api/latihan/<id>", methods=["PUT"])(LatihanController.update_latihan)
    app.route("/api/latihan/<id>", methods=["DELETE"])(LatihanController.delete_latihan)
    app.route("/api/latihan/<id>", methods=["GET"])(LatihanController.get_latihan_by_id)
    app.route("/api/latihan-user-tanggal", methods=["GET"])(LatihanController.get_user_latihan_tanggal)

    app.route('/api/gerakan', methods=['POST'])(GerakanController.create_gerakan)
    app.route('/api/gerakan', methods=['GET'])(GerakanController.get_all_gerakan)


    app.route("/api/riwayat", methods=["POST"])(riwayat_controller.simpan_riwayat)
    app.route("/api/riwayat", methods=["GET"])(riwayat_controller.ambil_riwayat)

    app.route("/api/riwayat-berat", methods=["POST"])(riwayat_berat_controller.simpan_riwayat_berat)
    app.route("/api/riwayat-berat/<email>", methods=["GET"])(riwayat_berat_controller.ambil_riwayat_berat)



    @require_api_key
    def get_data():
        return jsonify({"message": "Data accessed successfully!"})
    app.route("/api/data", methods=["GET"])(get_data)

    # ===================== #
    # 🖥️ HALAMAN WEB ADMIN (HTML)
    # ===================== #
    # @app.route("/buat-admin")
    # def buat_admin():
    #     password_hash = bcrypt.generate_password_hash("12345678").decode("utf-8")

    #     data_admin = {
    #         "email": "filamsimg@gmail.com",
    #         "nama": "filamsi",
    #         "password": password_hash
    #     }

    #     mongo.db.admin.insert_one(data_admin)
    #     return "Admin berhasil dibuat"



    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "admin_id" not in session:
                return redirect(url_for("login_admin"))
            return f(*args, **kwargs)
        return decorated_function

    @login_required
    def role_required(role):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if "role" not in session or session["role"] != role:
                    return "Akses ditolak: Anda tidak punya hak akses", 403
                return f(*args, **kwargs)
            return decorated_function
        return decorator

   
    @app.route("/login", methods=["GET", "POST"])
    def login_admin():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            admin = mongo.db.admin.find_one({"email": email})
            if admin and bcrypt.check_password_hash(admin["password"], password):
                session["admin_id"] = str(admin["_id"])
                session["admin_nama"] = admin.get("nama", "Admin")
                

                mongo.db.login_logs.insert_one({
                    "admin_id": admin["_id"],
                    "email": email,
                    "nama": admin.get("nama", "Admin"),
                    "waktu": datetime.utcnow(),
                    "ip": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent")
                })

                return redirect(url_for("dashboard"))

            return "Login gagal", 401

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout_admin():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/admin/logins")
    @login_required
    def login_logs():
        if "admin_id" not in session:
            return redirect(url_for("login"))
        logs = list(mongo.db.login_logs.find().sort("waktu", -1))
        return render_template("login_logs.html", logs=logs)

    @app.route('/')
    @login_required
    def dashboard():
        jumlah_gerakan = mongo.db.gerakan.count_documents({})
        jumlah_latihan = mongo.db.latihan.count_documents({})
        return render_template("dashboard.html", jumlah_gerakan=jumlah_gerakan, jumlah_latihan=jumlah_latihan)

    @app.route('/latihan')
    @login_required
    def latihan_page():
        data = mongo.db.latihan.find({})
        daftar_latihan = [serialize_latihan_with_detail(d) for d in data]
        daftar_gerakan = list(mongo.db.gerakan.find({})) 
        return render_template("latihan.html", daftar_latihan=daftar_latihan, daftar_gerakan=daftar_gerakan)

    @app.route('/latihan/tambah_latihan', methods=["POST"])
    @login_required
    def tambah_latihan():

        # Ambil data dari form
        nama_latihan = request.form.get("nama_latihan")
        durasi = request.form.get("durasi")
        tingkat = request.form.get("tingkat")
        tanggal = request.form.get("tanggal")

        # Ambil list nama gerakan dari form
        nama_gerakan_list = request.form.getlist("gerakan")  # <select name="gerakan" ...>

        # Validasi field wajib
        if not all([nama_latihan, durasi, tingkat, tanggal]) or len(nama_gerakan_list) == 0:
            return "Semua field wajib diisi", 400
        try:
            durasi = int(durasi)
        except ValueError:
            return "Durasi harus berupa angka", 400

        # Ubah nama_gerakan → gerakan_id (cari dari MongoDB)
        gerakan = []
        for nama in nama_gerakan_list:
            data = mongo.db.gerakan.find_one({"nama_gerakan": nama})
            if data:
                gerakan.append({"gerakan_id": str(data["_id"])})
            else:
                return f"Gerakan '{nama}' tidak ditemukan", 400

        jumlah = len(gerakan)
        tingkat = tingkat.capitalize()

        # Upload gambar
        file_gambar = request.files.get("gambar")
        filename_gambar = None
        if file_gambar and file_gambar.filename:
            ext = file_gambar.filename.rsplit('.', 1)[-1].lower()
            filename_gambar = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs("upload/gambar", exist_ok=True)
            file_gambar.save(os.path.join("upload/gambar", filename_gambar))

        # Simpan ke MongoDB
        mongo.db.latihan.insert_one({
            "nama_latihan": nama_latihan,
            "durasi": durasi,
            "jumlah": jumlah,
            "tingkat": tingkat,
            "tanggal": tanggal,
            "gambar": filename_gambar,
            "gerakan": gerakan,
            "created_at": datetime.utcnow()
        })

        return redirect(url_for("latihan_page"))

    @app.route('/latihan/edit/<id>', methods=["POST"])
    @login_required
    def edit_latihan(id):
        latihan = mongo.db.latihan.find_one({"_id": ObjectId(id)})
        if not latihan:
            return "Latihan tidak ditemukan", 404

        # Ambil data dari form
        nama_latihan = request.form.get("nama_latihan")
        durasi = request.form.get("durasi")
        tingkat = request.form.get("tingkat")
        tanggal = request.form.get("tanggal")
        nama_gerakan_list = request.form.getlist("gerakan")

        if not all([nama_latihan, durasi, tingkat, tanggal]) or not nama_gerakan_list:
            return "Field tidak lengkap", 400

        try:
            durasi = int(durasi)
        except ValueError:
            return "Durasi harus angka", 400

        gerakan = []
        for nama in nama_gerakan_list:
            data = mongo.db.gerakan.find_one({"nama_gerakan": nama})
            if data:
                gerakan.append({"gerakan_id": str(data["_id"])})

        jumlah = len(gerakan)
        tingkat = tingkat.capitalize()

        # Cek apakah user upload gambar baru
        file_gambar = request.files.get("gambar")
        filename_gambar = latihan.get("gambar")
        if file_gambar and file_gambar.filename:
            ext = file_gambar.filename.rsplit('.', 1)[-1].lower()
            filename_gambar = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs("upload/gambar", exist_ok=True)
            file_gambar.save(os.path.join("upload/gambar", filename_gambar))

        # Update ke MongoDB
        mongo.db.latihan.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "nama_latihan": nama_latihan,
                "durasi": durasi,
                "jumlah": jumlah,
                "tingkat": tingkat,
                "tanggal": tanggal,
                "gambar": filename_gambar,
                "gerakan": gerakan
            }}
        )

        return redirect(url_for("latihan_page"))

    @app.route('/latihan/hapus/<id>', methods=["POST"])
    @login_required 
    def hapus_latihan(id):
        try:
            mongo.db.latihan.delete_one({"_id": ObjectId(id)})
            return redirect(url_for("latihan_page"))
        except Exception as e:
            return f"Gagal menghapus latihan: {e}", 500


    @app.route('/gerakan')
    @login_required
    def gerakan_page():
        data = mongo.db.gerakan.find({})
        daftar_gerakan = [serialize_gerakan(d) for d in data]
        return render_template("gerakan.html", daftar_gerakan=daftar_gerakan)

    @app.route('/gerakan/tambah', methods=["POST"])
    @login_required    
    def tambah_gerakan():
        nama = request.form.get("nama_gerakan")
        durasi = request.form.get("durasi")
        instruksi = request.form.get("instruksi")
        repetisi = request.form.get("repetisi")
        gambar = request.files.get("gambar")

        if not nama or not repetisi:
            return "Nama dan repetisi wajib diisi", 400

        data = {
            "nama_gerakan": nama,
            "instruksi": instruksi,
            "repetisi": int(repetisi),
            "durasi": int(durasi)
        }

        if gambar and gambar.filename:
            ext = gambar.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs("upload/gerakan", exist_ok=True)
            gambar.save(os.path.join("upload/gerakan", filename))
            data["gambar"] = filename

        mongo.db.gerakan.insert_one(data)
        return redirect(url_for("gerakan_page"))

    @app.route('/gerakan/edit/<id>', methods=["POST"])
    @login_required
    def edit_gerakan(id):
        gerakan = mongo.db.gerakan.find_one({"_id": ObjectId(id)})
        if not gerakan:
            return "Gerakan tidak ditemukan", 404

        nama = request.form.get("nama_gerakan")
        instruksi = request.form.get("instruksi")
        durasi = request.form.get("durasi")
        repetisi = request.form.get("repetisi")
        gambar = request.files.get("gambar")

        update_data = {
            "nama_gerakan": nama,
            "instruksi": instruksi,
            "repetisi": int(repetisi),
            "durasi": int(durasi),
        }

        if gambar and gambar.filename:
            ext = gambar.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs("upload/gerakan", exist_ok=True)
            gambar.save(os.path.join("upload/gerakan", filename))
            update_data["gambar"] = filename

        mongo.db.gerakan.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        return redirect(url_for("gerakan_page"))

    @app.route('/gerakan/hapus/<id>', methods=["POST"])
    @login_required
    def hapus_gerakan(id):
        mongo.db.gerakan.delete_one({"_id": ObjectId(id)})
        return redirect(url_for("gerakan_page"))


