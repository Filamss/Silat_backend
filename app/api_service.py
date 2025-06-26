from flask_jwt_extended import create_access_token
from datetime import timedelta

def generate_token(identity):
    return create_access_token(identity=identity, expires_delta=timedelta(days=1))
