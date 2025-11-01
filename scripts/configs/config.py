from datetime import timedelta

# Configurações da API
class Config:
    SECRET_KEY = 'chave_secreta'
    CACHE_TYPE = 'simple'
    ###########DOC#########################33
    SWAGGER = {
        'title': 'API DE LIVROS',
        'uiversion': 3
    }
    ###########DOC#########################33
    SQLALCHEMY_DATABASE_URI = 'sqlite:///books.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'chave_secreta'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JSON_SORT_KEYS = False
