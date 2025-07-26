# Health Assistant: Technical Architecture Documentation

## 🏗️ System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Storage &     │
│                 │    │   Pipeline      │    │   Retrieval     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • MedQuAD XML   │───▶│ • XML Parser    │───▶│ • ChromaDB      │
│ • MedlinePlus   │    │ • Web Scraper   │    │ • Vector Store  │
│   Encyclopedia  │    │ • Text Cleaner  │    │ • Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │◀───│   RAG Pipeline  │◀───│   LLM (Gemini)  │
│                 │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Natural       │    │ • Query         │    │ • Context       │
│   Language      │    │   Embedding     │    │   Synthesis     │
│ • Medical       │    │ • Semantic      │    │ • Answer        │
│   Questions     │    │   Search        │    │   Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📊 Data Flow Architecture

### 1. **Data Ingestion Layer**
```
MedQuAD XML Files ──┐
                     ├──▶ Document Processor ──▶ ChromaDB
MedlinePlus Web ────┘
```

**Key Components:**
- **XML Parser**: Extracts Q&A pairs from MedQuAD XML structure
- **Web Scraper**: Crawls MedlinePlus A-Z index pages for article links
- **Content Extractor**: Pulls article content from individual pages
- **Text Normalizer**: Cleans and standardizes text format

### 2. **Vector Storage Layer**
```
Raw Documents ──▶ Embedding Function ──▶ ChromaDB Collection
                                    │
                                    ▼
                              Metadata Store
                              (source, title, URL)
```

**Technical Details:**
- **Embedding Model**: ChromaDB's default embedding function
- **Vector Dimensions**: 1536 (default)
- **Similarity Metric**: Cosine similarity
- **Persistence**: Local disk storage (`chroma_persistent_storage/`)

### 3. **Retrieval Layer**
```
User Query ──▶ Query Embedding ──▶ K-NN Search ──▶ Top-K Documents
```

**Search Parameters:**
- **K**: 5 (configurable)
- **Search Strategy**: Semantic similarity
- **Filtering**: None (retrieves from all sources)

### 4. **Generation Layer**
```
Retrieved Context ──▶ Prompt Engineering ──▶ Gemini LLM ──▶ Final Answer
```

**Prompt Structure:**
```
You are a medical assistant. Based on the following medical information, 
answer the user's question. If the information provided doesn't contain 
the answer, say so clearly.

Medical Information:
{retrieved_context}

User Question: {user_question}

Please provide a clear, accurate, and helpful answer based on the 
medical information above.
```

---

## 🔧 Implementation Details

### **Data Processing Pipeline**

#### MedQuAD Processing (`process_medquad_data.py`)
```python
def extract_qa_from_xml(xml_content):
    """Extract Q&A pairs from XML structure"""
    root = ET.fromstring(xml_content)
    qa_pairs = []
    
    for qa_pair in root.findall('.//QAPair'):
        question = qa_pair.find('Question').text
        answer = qa_pair.find('Answer').text
        qa_pairs.append({'question': question, 'answer': answer})
    
    return qa_pairs
```

**XML Structure Parsed:**
```xml
<QAPair pid="1">
    <Question qid="0000043_1-1">What is Vulvar Cancer?</Question>
    <Answer>Key Points - Vulvar cancer is a rare disease...</Answer>
</QAPair>
```

#### MedlinePlus Scraping (`scrape_medlineplus.py`)
```python
def get_article_links_from_index(index_url):
    """Extract article links from A-Z index pages"""
    soup = BeautifulSoup(response.content, 'html.parser')
    index_ul = soup.find('ul', {'id': 'index'})
    
    for link in index_ul.find_all('a', href=True):
        href = link['href']
        if href.startswith('article/') and href.endswith('.htm'):
            # Process article link
```

**Scraping Strategy:**
1. **Index Discovery**: Find A-Z index pages from main encyclopedia page
2. **Link Extraction**: Extract article links from each index page
3. **Content Scraping**: Pull article content from individual pages
4. **Rate Limiting**: 1-second delay between requests (respectful scraping)

### **Vector Database Schema**

#### Document Structure
```python
{
    "id": "unique_document_id",
    "text": "Question: {question}\nAnswer: {answer}",
    "metadata": {
        "question": "Original question text",
        "answer": "Original answer text", 
        "source_file": "MedQuAD file path",
        "source": "MedlinePlus Encyclopedia" (for MedlinePlus),
        "url": "Article URL" (for MedlinePlus)
    }
}
```

#### ChromaDB Collection Configuration
```python
collection = chroma_client.get_or_create_collection(
    name="medquad_qa_collection",
    # Uses default embedding function
    # Default similarity metric: cosine
)
```

### **Query Processing Pipeline**

#### 1. Query Embedding
```python
results = collection.query(
    query_texts=[user_question],
    n_results=5  # Top-K retrieval
)
```

#### 2. Context Assembly
```python
context = "\n\n".join(results['documents'][0])
```

#### 3. LLM Generation
```python
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=prompt
)
```

---

## 🎯 Technical Decisions & Trade-offs

### **Why ChromaDB?**
- **Pros**: 
  - Simple setup (no external dependencies)
  - Good performance for small-medium datasets
  - Built-in embedding functions
  - Persistent storage
- **Cons**: 
  - Limited scalability for very large datasets
  - No advanced features like hybrid search

### **Why Gemini 2.0 Flash?**
- **Pros**:
  - Fast inference (good for real-time queries)
  - Good medical knowledge
  - Cost-effective
- **Cons**:
  - Less powerful than larger models
  - Limited context window

### **Why This Data Combination?**
- **MedQuAD**: Structured Q&A format, good for specific questions
- **MedlinePlus**: Comprehensive articles, good for detailed explanations
- **Combination**: Covers both specific and general medical queries

### **Scraping vs. API**
- **Scraping Choice**: MedlinePlus doesn't provide a public API
- **Rate Limiting**: 1-second delays to be respectful
- **Robustness**: Error handling for network issues

---

## 🔍 Performance Characteristics

### **Data Processing**
- **MedQuAD**: ~1000-2000 Q&A pairs per minute
- **MedlinePlus**: ~60 articles per minute (due to rate limiting)
- **Total Processing Time**: ~2-3 hours for full dataset

### **Query Performance**
- **Retrieval Time**: <100ms (ChromaDB)
- **LLM Generation**: 2-5 seconds (Gemini)
- **Total Response Time**: 2-6 seconds

### **Storage Requirements**
- **Vector Storage**: ~500MB for full dataset
- **Metadata**: ~50MB
- **Total**: ~550MB

---

## 🚀 Scalability Considerations

### **Current Limitations**
- Single-threaded processing
- No distributed storage
- Limited context window (Gemini)

### **Future Improvements**
- **Parallel Processing**: Multi-threaded scraping
- **Distributed Storage**: Redis/PostgreSQL for metadata
- **Advanced Retrieval**: Hybrid search (keyword + semantic)
- **Caching**: Redis for frequent queries
- **Model Upgrades**: Larger context windows

---

## 🔒 Security & Ethics

### **Data Privacy**
- No user data stored
- All medical data is public domain
- No PII in the system

### **Medical Disclaimer**
- **Educational Use Only**: Not for medical diagnosis
- **Source Attribution**: All answers cite sources
- **Accuracy**: Based on authoritative sources (NIH/NLM)

### **Rate Limiting**
- Respectful web scraping (1-second delays)
- No aggressive crawling
- Follows robots.txt

---

## 🧪 Testing & Validation

### **Data Quality Checks**
- XML parsing validation
- Content length filtering (>100 characters)
- Duplicate detection

### **Retrieval Quality**
- Manual evaluation of top-K results
- Relevance scoring
- Source diversity

### **Answer Quality**
- Fact-checking against sources
- Consistency validation
- Medical accuracy review

---

This technical architecture provides a robust foundation for medical question answering while maintaining transparency, accuracy, and ethical use of medical information. 