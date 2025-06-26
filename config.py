from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Database Configuration
MONGO_URI = os.getenv("MONGO_URI")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET")

# Email Configuration
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_SERVER = os.getenv("MAIL_SERVER")

# Safely convert MAIL_PORT to int
try:
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
except ValueError:
    MAIL_PORT = 587  # fallback default

# Convert MAIL_USE_TLS to boolean safely
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").strip().lower() in ("true", "1", "yes")
