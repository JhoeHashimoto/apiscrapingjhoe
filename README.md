# API de Scrapping de Livros e ML

Este projeto implementa uma API Flask para servir dados de livros extraídos por web scraping do site `books.toscrape.com`.

## Setup Local

    ```
    API_SCRAPPING_LIVROS_BOOKS_JHOE/
    ├── .env                # Arquivo de variáveis de ambiente (local)
    ├── .venv/              # Ambiente virtual Python
    ├── app.py              # Ponto de entrada da aplicação Flask (a API)
    ├── instance/
    │   └── books.db        # Banco de dados (Ex: SQLite, gerado pela app)
    ├── README.md           # Este arquivo
    ├── requirements.txt    # Dependências do projeto
    ├── scripts/            # Scripts de-para (ETL, scraping, etc.)
    │   ├── configs/
    │   ├── docstream/
    │   └── scrapper/       # Módulo do web scraper
    ├── STORAGE_DATA/
    │   └── RAW_ZONE/       # Destino dos dados brutos do scraping
    │       ├── 2025-10-25.../
    │       └── ...
    └── vercel.json         # Configuração de deploy para a Vercel
    ```

1.  **Crie um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # (ou .\\venv\\Scripts\\activate no Windows)
    venv\Scripts\activate    #CMD
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute a subida da API:**
    ```bash
    python app.py
    ```

5.  **Inicie a API (Modo de Debug):**
    ```bash
    flask run
    ```
    A API estará disponível em `http://127.0.0.1:5000`.
    A documentação do Swagger estará em `http://127.0.0.1:5000/apidocs`.


6.  **O scrapping é realizado através do endpoint**
    ```bash
    POST em `/api/v1/scraping/trigger`.
    ```

## Deploy na Vercel

1.  Faça o push do seu código para um repositório (GitHub, GitLab, etc.).
2.  Importe o projeto no dashboard da Vercel.
3.  Faça o deploy.

