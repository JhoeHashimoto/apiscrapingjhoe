import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
from datetime import datetime, timezone
import concurrent.futures
import os
BASE_URL = 'https://books.toscrape.com/'
CATALOGUE_URL = 'https://books.toscrape.com/catalogue/'

MAX_WORKERS = 50   #-----------------> Definir a quantidade de workers

def parse_book_page(book_url):
    """
    Extrai dados de uma ÚNICA página de livro.
    """
    try:
        response = requests.get(book_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        product_table = soup.find('table', class_='table-striped')
        rows = product_table.find_all('tr')
        
        title = soup.find('h1').text
        price = soup.find('p', class_='price_color').text.replace('£', '')
        availability_text = rows[5].find('td').text
        availability = re.search(r'\((\d+) available\)', availability_text).group(1)
        star_rating_class = soup.find('p', class_='star-rating')['class'][1]
        rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
        rating = rating_map.get(star_rating_class, 0)
        category = soup.find('ul', class_='breadcrumb').find_all('a')[2].text
        image_relative_url = soup.find('div', class_='item active').find('img')['src']
        image_url = urljoin(BASE_URL, image_relative_url.replace('../', ''))
        upc = rows[0].find('td').text
        return {
            'upc': upc,
            'title': title,
            'price_gbp': float(price),
            'rating': rating,
            'availability': int(availability),
            'category': category,
            'image_url': image_url,
            'source_url': book_url,
            'dt_ingestao': datetime.now()
        }
    except Exception as e:
        print(f"Erro ao processar o livro {book_url}: {e}")
        return None

def run_scraping(app, db, Books):
    """
    Executa o scraping em duas fases:
    1. Coleta todas as URLs dos livros sequencialmente.
    2. Processa todas as URLs dos livros em paralelo.
    """
    now = datetime.now()
    inicio = datetime.now()
    print("Hora inicial:", inicio.strftime("%H:%M:%S"))
    print("Iniciando processo de scraping...")
    print("#################################")

    timestamp_folder = now.strftime('%Y-%m-%d_%H-%M-%S')
    target_directory = os.path.join('STORAGE_DATA/RAW_ZONE', timestamp_folder)
    os.makedirs(target_directory, exist_ok=True)
    file_name = f"{timestamp_folder}_books_extraction.csv"
    output_file_path = os.path.join(target_directory, file_name)

    # --- FASE 1: Coletar todas as URLs dos livros ---
    print(f"FASE 1: Coletando todas as URLs dos livros...")
    book_urls_to_scrape = []
    current_page_url = urljoin(CATALOGUE_URL, 'page-1.html')
    page_num = 1
    
    while True:
        print(f"Coletando URLs da página: {page_num}...")
        try:
            response = requests.get(current_page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            book_items = soup.find_all('article', class_='product_pod')
            if not book_items:
                break 

            for book in book_items:
                book_relative_url = book.find('h3').find('a')['href']
                book_absolute_url = urljoin(CATALOGUE_URL, book_relative_url)
                book_urls_to_scrape.append(book_absolute_url)
            
            next_page_link = soup.find('li', class_='next')
            if next_page_link:
                next_page_relative_url = next_page_link.find('a')['href']
                current_page_url = urljoin(CATALOGUE_URL, next_page_relative_url)
                page_num += 1
            else:
                break
        except Exception as e:
            print(f"Erro ao processar a página de catálogo {current_page_url}: {e}")
            break
            
    total_books = len(book_urls_to_scrape)
    print(f"FASE 1 Concluída: {total_books} URLs de livros coletadas.")
    print("--------------------------------------------------") 
    print(f"FASE 2: Processando {total_books} livros usando {MAX_WORKERS} threads...")
    
    # --- FASE 2: Processar as URLs em Paralelo ---
    all_books_data = []
    completed_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        futures = [executor.submit(parse_book_page, url) for url in book_urls_to_scrape]

        for future in concurrent.futures.as_completed(futures):
            completed_count += 1
            
            try:
                book_data = future.result() 
                
                if book_data:
                    all_books_data.append(book_data)
                    
                    if completed_count % 50 == 0 or completed_count == total_books:
                        print(f"[PROGRESSO] {completed_count}/{total_books} livros processados.")
                        
                else:
                   
                    print(f"[AVISO] Tarefa concluída com falha. Progresso: {completed_count}/{total_books}")
                    
            except Exception as e:
                print(f"[ERRO CRÍTICO] Erro na thread [Progresso: {completed_count}/{total_books}]: {e}")

    # --- FIM DA FASE 2 ---

    print("--------------------------------------------------")
    print(f"FASE 2 Concluída: {len(all_books_data)} livros processados com sucesso.")
    status_scrapping = None
    if all_books_data:
        df = pd.DataFrame(all_books_data)
        
        # Adiciona o timestamp UMA VEZ ao DataFrame final
        ingestion_timestamp = datetime.now(timezone.utc).isoformat()
        df['dt_ingestao'] = ingestion_timestamp
        df['file_path'] = output_file_path
        # Reordena as colunas
        columns_order = [
            'upc','title','price_gbp','rating','availability','category','image_url',
            'source_url','dt_ingestao','file_path']

        df = df[columns_order]

        if not df.empty:
            print("Iniciando salvamento no Cloud Storage...")
            df.to_csv(output_file_path, index=False, encoding='utf-8')
            print("Iniciando salvamento no banco de dados...")
            try:
                
                with app.app_context():
                    df = df.astype(str)

                    db.session.query(Books).delete()
                    print("Tabela 'books' truncada.")

                    data_to_insert = df.to_dict(orient='records')
                    
                    db.session.bulk_insert_mappings(Books, data_to_insert)
                    print(f"Inseridos {len(data_to_insert)} registros no banco.")
                    
                    db.session.commit()
                    print("Commit realizado no banco de dados.")
                    status_scrapping = 'Sucesso'
                    
            except Exception as e:
                print(f"ERRO ao salvar no banco de dados: {e}")
                db.session.rollback()
                status_scrapping = f'Falha no DB: {e}'

        fim = datetime.now()
        print("Hora final:", fim.strftime("%H:%M:%S"))
        print(f"Scraping concluído! Dados salvos em: {output_file_path}")
        status_scrapping = 'Sucesso'
        delta = (fim - inicio).total_seconds() / 60
        print(f"Tempo decorrido: {delta:.2f} minutos")
        
    else:
        print("Nenhum dado foi extraído.")

    return status_scrapping, output_file_path, delta