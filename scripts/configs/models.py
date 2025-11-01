
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Books(db.Model):
    upc = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    price_gbp = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    source_url = db.Column(db.String(255), nullable=False)
    dt_ingestao = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)