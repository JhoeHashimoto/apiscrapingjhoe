from flask import Flask, jsonify, request
import requests
from flasgger import Swagger, swag_from
from scripts.configs.config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity, create_refresh_token)
import os
from datetime import datetime
from scripts.scrapper.scrapper import run_scraping
from scripts.configs.models import db, User, Books

app = Flask(__name__)             #Instancia a app
app.config.from_object(Config)    #Instancia a classe Config do config.py
swagger = Swagger(app)            #Instancia o Swagger

# Gerenciador do JWT
jwt = JWTManager(app)

# ORM banco
db.init_app(app)

# ROTA RAIZ
@app.route('/')
def home():
    return "PÁGINA INICIAL, API DE LIVROS"

# ROTA de Cadastro
@app.route('/api/v1/auth/register', methods=['POST'])
@swag_from('scripts/docstream/post_register.yml')
def register_user():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 400

    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

# ROTA de Login
@app.route('/api/v1/auth/login', methods=['POST'])
@swag_from('scripts/docstream/post_login.yml')
def login():
      data = request.get_json()
      user = User.query.filter_by(username=data['username']).first()
      if user and user.password == data['password']:
          access_token = create_access_token(identity=str(user.id))     #<----------------------------------------- CRIA O TOKEN DE ACESSO
          refresh_token = create_refresh_token(identity=str(user.id))   #<----------------------------------------- CRIA O TOKEN DE REFRESH, para acessar /refresh e gerar o novo access_token
          return jsonify(access_token = access_token,refresh_token=refresh_token), 200
      return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/v1/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)                                                         # <-- Exige o REFRESH token criado no /login
@swag_from('scripts/docstream/post_refresh.yml')
def refresh():
    current_user_id = get_jwt_identity()                                            
    new_access_token = create_access_token(identity=current_user_id)                #<--- Cria um NOVO access token para ele
    return jsonify(access_token=new_access_token), 200                              #<-- # Retorna o novo access token para o frontend

# ROTA SCRAPPER Trigger
@app.route('/api/v1/scraping/trigger', methods=['POST'])
@jwt_required()
@swag_from('scripts/docstream/post_scraping_trigger.yml')
def run_scrapper():

    status_scrapping, output_file_path, delta = run_scraping(app, db, Books)
   
    return jsonify(
            status = status_scrapping,
            message="Scraping concluído com sucesso!",
            output_file=output_file_path,
            tempo_decorrido_minutos=round(delta, 2)
        ), 200

# ROTA GET para todos os Livros
@app.route('/api/v1/books', methods=['GET'])
@jwt_required()
@swag_from('scripts/docstream/get_all_books.yml')
def get_all_books():
    try:
        all_books = Books.query.all()

        results = [
            {
                "upc": book.upc,
                "title": book.title,
                "price_gbp": book.price_gbp,
                "rating": book.rating,
                "availability": book.availability,
                "category": book.category,
                "image_url": book.image_url,
                "source_url": book.source_url
            }
            for book in all_books
        ]
        return jsonify(results), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

# ROTA Books search by upc
@app.route('/api/v1/books/<string:upc>', methods=['GET'])
@jwt_required()
@swag_from('scripts/docstream/get_book_by_upc.yml')
def get_book_by_upc(upc):
    try:
        book = Books.query.get_or_404(upc)

        result = {
            "upc": book.upc,
            "title": book.title,
            "price_gbp": book.price_gbp,
            "rating": book.rating,
            "availability": book.availability,
            "category": book.category,
            "image_url": book.image_url,
            "source_url": book.source_url
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

# ROTA Books/Search by title and category
@app.route('/api/v1/books/search', methods=['GET'])
@jwt_required()
@swag_from('scripts/docstream/get_book_by_title_&_category.yml')
def search_books():
    try:
        query_title = request.args.get('title')
        query_category = request.args.get('category')

        base_query = Books.query

        if query_title:
            
            base_query = base_query.filter(Books.title.ilike(f'%{query_title}%'))

        if query_category:
            base_query = base_query.filter(Books.category.ilike(f'%{query_category}%'))

        books = base_query.all()

        results = [
            {
                "upc": book.upc,
                "title": book.title,
                "price_gbp": book.price_gbp,
                "rating": book.rating,
                "availability": book.availability,
                "category": book.category,
                "image_url": book.image_url,
                "source_url": book.source_url
            }
            for book in books
        ]
        return jsonify(results), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
    
# ROTA Categorias
@app.route('/api/v1/categories/', methods=['GET'])
@jwt_required()
@swag_from('scripts/docstream/get_all_books.yml')
def get_all_categories():
    try:
        # 1. Busca todos os registros da tabela 'Books'
        all_books = Books.query.all()

        results = [book.category for book in all_books]
        
        return jsonify(results), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

# ROTA Health
@app.route('/api/v1/health', methods=['GET'])
@jwt_required()
@swag_from('scripts/docstream/get_health.yml')
def health_check_liveness():
    return jsonify(status="OK, API no ar!"), 200

# Inicialização banco
def init_db(application):
    """Cria as tabelas do banco de dados se não existirem."""

    with application.app_context():
        db.create_all()
        print("Banco de dados verificado/criado com sucesso.")

if __name__ == '__main__':
    init_db(app)
    app.run(debug=True)