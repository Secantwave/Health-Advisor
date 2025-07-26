"""
MedlinePlus Encyclopedia Scraper (A-Z Index Version)
This script scrapes medical articles from MedlinePlus and adds them to the existing ChromaDB collection.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

# ChromaDB setup
collection_name = "medquad_qa_collection"
chroma_client = chromadb.PersistentClient(path="chroma_persistent_storage")
collection = chroma_client.get_or_create_collection(name=collection_name)

BASE_URL = "https://medlineplus.gov"
ENCYCLOPEDIA_URL = "https://medlineplus.gov/encyclopedia.html"


def get_index_links():
    """Get all A-Z, 0-9 index page links from the main encyclopedia page."""
    print("Fetching A-Z,0-9 index links...")
    try:
        response = requests.get(ENCYCLOPEDIA_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        index_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Match both ency/encyclopedia_A.htm and /ency/encyclopedia_A.htm
            if re.match(r"^/?ency/encyclopedia_[A-Z0-9]\.htm$", href):
                full_url = urljoin(BASE_URL, href)
                index_links.append(full_url)
        print(f"Found {len(index_links)} index pages.")
        return index_links
    except Exception as e:
        print(f"Error fetching index links: {e}")
        return []

def get_article_links_from_index(index_url):
    """Get all article links from an index page (A-Z,0-9)."""
    try:
        response = requests.get(index_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        article_links = []
        index_ul = soup.find('ul', {'id': 'index'})
        if not index_ul:
            print(f"No <ul id='index'> found in {index_url}")
            return []
        for link in index_ul.find_all('a', href=True):
            href = link['href']
            if href.startswith('article/') and href.endswith('.htm'):
                full_url = urljoin(index_url, href)
                anchor_title = link.get_text(strip=True)
                article_links.append({'url': full_url, 'anchor_title': anchor_title})
        return article_links
    except Exception as e:
        print(f"Error fetching articles from {index_url}: {e}")
        return []

def scrape_article_content(url, anchor_title):
    """Scrape content from a single encyclopedia article, always using <h1> as title if available."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Get title from <h1> if available
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else anchor_title
        content_div = soup.find('div', {'id': 'ency_content'})
        if not content_div:
            return None
        content_text = content_div.get_text(separator=' ', strip=True)
        content_text = re.sub(r'\s+', ' ', content_text).strip()
        if len(content_text) < 100:
            return None
        return {
            'title': title,
            'content': content_text,
            'url': url
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def add_medlineplus_to_chroma(articles, batch_size=50):
    print("Adding MedlinePlus articles to ChromaDB...")
    documents = []
    for i, article in enumerate(articles):
        if article:
            doc_id = f"medlineplus_{i+1}"
            doc_text = f"Title: {article['title']}\nContent: {article['content']}"
            documents.append({
                'id': doc_id,
                'text': doc_text,
                'title': article['title'],
                'content': article['content'],
                'source': 'MedlinePlus Encyclopedia',
                'url': article['url']
            })
    total_docs = len(documents)
    added_docs = 0
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        ids = [doc["id"] for doc in batch]
        texts = [doc["text"] for doc in batch]
        metadatas = [{
            "title": doc["title"],
            "content": doc["content"],
            "source": doc["source"],
            "url": doc["url"]
        } for doc in batch]
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        added_docs += len(batch)
        print(f"Added batch {i//batch_size + 1}: {len(batch)} articles (Total: {added_docs}/{total_docs})")
    print(f"Successfully added {added_docs} MedlinePlus articles to ChromaDB")

def main():
    print("=== MedlinePlus Encyclopedia Scraper (A-Z Index Version) ===")
    print("This will scrape medical articles from MedlinePlus and add them to your knowledge base.")
    index_links = get_index_links()
    if not index_links:
        print("No index pages found. Exiting.")
        return
    all_article_links = []
    for idx_url in index_links:
        print(f"Fetching articles from {idx_url}")
        links = get_article_links_from_index(idx_url)
        all_article_links.extend(links)
        time.sleep(1)
    print(f"Total articles found: {len(all_article_links)}")
    max_articles = input("Number of articles to scrape (default: 100, 'all' for all): ").strip()
    if max_articles.lower() == 'all':
        max_articles = len(all_article_links)
    else:
        max_articles = int(max_articles) if max_articles.isdigit() else 100
    all_article_links = all_article_links[:max_articles]
    print(f"Will scrape {len(all_article_links)} articles")
    articles = []
    for i, link_info in enumerate(all_article_links):
        print(f"Scraping {i+1}/{len(all_article_links)}: {link_info['anchor_title']}")
        article = scrape_article_content(link_info['url'], link_info['anchor_title'])
        if article:
            articles.append(article)
        time.sleep(1)
    print(f"Successfully scraped {len(articles)} articles")
    if articles:
        add_medlineplus_to_chroma(articles)
        print(f"\nTotal documents in collection: {collection.count()}")
        print("MedlinePlus articles have been added to your knowledge base!")
    else:
        print("No articles were successfully scraped.")

if __name__ == "__main__":
    main() 