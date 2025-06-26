from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
import config
import os

app = Flask(__name__)
app.config["MONGO_URI"] = config.MONGO_URI
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.secret_key = os.getenv("SECRET_KEY", "dev-secret") 

CORS(app)
jwt = JWTManager(app)
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

try:
    mongo.cx.server_info()
    print("✅ MongoDB connected successfully.")
except Exception as e:
    print("❌ Failed to connect to MongoDB:", e)
