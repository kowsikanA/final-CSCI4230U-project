from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Shared database object used across the app 
db = SQLAlchemy()

# Shared JWT manager used to create and validate access tokens
jwt = JWTManager()
