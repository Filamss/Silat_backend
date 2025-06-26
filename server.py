import os
from flask import send_from_directory
from app import app
from dotenv import load_dotenv
from app.routes import init_routes

load_dotenv()


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_GAMBAR_FOLDER = os.path.join(BASE_DIR, 'upload', 'gambar')
UPLOAD_GERAKAN_FOLDER = os.path.join(BASE_DIR, 'upload', 'gerakan')

@app.route('/upload/gambar/<filename>')
def serve_gambar(filename):
    return send_from_directory(UPLOAD_GAMBAR_FOLDER, filename)

@app.route('/upload/gerakan/<filename>')
def serve_gerakan(filename):
    return send_from_directory(UPLOAD_GERAKAN_FOLDER, filename)

init_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
