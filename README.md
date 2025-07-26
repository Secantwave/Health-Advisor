# Health Assistant: Medical RAG System

Welcome to the Health Assistant project! This is a Retrieval-Augmented Generation (RAG) system for medical question answering, combining structured Q&A from MedQuAD and authoritative articles from MedlinePlus.

## 🚀 Project Overview
- **Goal:** Provide accurate, explainable, and up-to-date medical answers using a combination of trusted datasets and LLMs.
- **Data Sources:**
  - **MedQuAD:** Medical Q&A pairs from NIH and other reputable sources (XML format)
  - **MedlinePlus:** 4,000+ encyclopedia articles from the U.S. National Library of Medicine (scraped live)
- **Retrieval:** All data is indexed in [ChromaDB](https://www.trychroma.com/) for fast semantic search.
- **Generation:** Uses Google Gemini LLM for answer synthesis.

---

## 🛠️ Setup Instructions

1. **Clone the repository and install dependencies:**
   ```bash
   git clone <your-repo-url>
   cd Health Assistant
   python -m venv env
   env\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

2. **Set up your environment variables:**
   - Create a `.env` file with your Gemini API key:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

3. **Directory Structure:**
   ```
   Health Assistant/
   ├── MedQuAD/                # MedQuAD XML dataset (place here)
   ├── chroma_persistent_storage/ # ChromaDB vector storage
   ├── process_medquad_data.py # Script to process MedQuAD
   ├── scrape_medlineplus.py   # Script to scrape MedlinePlus
   ├── query_medical_qa.py     # Query interface
   ├── requirements.txt
   └── README.md
   ```

---

## 📚 Data Processing Pipeline

### 1. **Process MedQuAD Data**
- **Purpose:** Parse all XML Q&A pairs and store them in ChromaDB.
- **Run:**
  ```bash
  python process_medquad_data.py
  ```
- **Options:**
  - Test mode (processes a small subset)
  - Full mode (processes all files)

### 2. **Scrape MedlinePlus Encyclopedia**
- **Purpose:** Scrape all A-Z medical articles and add them to ChromaDB.
- **Run:**
  ```bash
  python scrape_medlineplus.py
  ```
- **Options:**
  - Choose how many articles to scrape (start with 100 for testing, or 'all' for the full set)

### 3. **Query the Knowledge Base**
- **Purpose:** Ask medical questions and get answers synthesized from both MedQuAD and MedlinePlus.
- **Run:**
  ```bash
  python query_medical_qa.py
  ```
- **Features:**
  - Interactive mode (ask multiple questions)
  - Single question mode
  - Shows sources for every answer

---

## 🧠 How It Works
1. **Ingestion:**
   - MedQuAD XMLs are parsed for Q&A pairs.
   - MedlinePlus articles are scraped and parsed for title/content.
2. **Indexing:**
   - All documents are embedded and stored in ChromaDB for semantic search.
3. **Retrieval:**
   - For each user question, the top relevant documents are retrieved.
4. **Generation:**
   - The Gemini LLM is prompted with the retrieved context to generate a final answer.
5. **Transparency:**
   - The sources (Q&A or article titles/URLs) are shown for every answer.


## 🤖 Example Usage

```bash
# Process MedQuAD (once)
python process_medquad_data.py

# Scrape MedlinePlus (once)
python scrape_medlineplus.py

# Query the system
python query_medical_qa.py
```

---

## 📄 License & Credits
- MedQuAD: [NIH License](https://www.nlm.nih.gov/databases/download/medquad.html)
- MedlinePlus: [A.D.A.M. Medical Encyclopedia](https://medlineplus.gov/encyclopedia.html)
- ChromaDB, Google Gemini: see respective licenses

---

## 🙋‍♂️ Team & Contact
- Built for [Your Hackathon Name]
- Team: [Your Team Name]
- Contact: [Your Email or Discord]

---

**Good luck and have fun hacking!** 
