"""
MedQuAD Data Processor
This script processes all XML files from the MedQuAD dataset and stores them in ChromaDB.
Run this once to create your knowledge base, then use query_medical_qa.py for queries.
"""

from dotenv import load_dotenv
import chromadb
import os
import xml.etree.ElementTree as ET
import time

load_dotenv()

# ChromaDB setup
collection_name = "medquad_qa_collection"
chroma_client = chromadb.PersistentClient(path="chroma_persistent_storage")
collection = chroma_client.get_or_create_collection(name=collection_name)

def extract_qa_from_xml(xml_content):
    """Extract question-answer pairs from XML content"""
    try:
        root = ET.fromstring(xml_content)
        qa_pairs = []
        
        # Find all QAPair elements
        for qa_pair in root.findall('.//QAPair'):
            question_elem = qa_pair.find('Question')
            answer_elem = qa_pair.find('Answer')
            
            if question_elem is not None and answer_elem is not None:
                question = question_elem.text.strip() if question_elem.text else ""
                answer = answer_elem.text.strip() if answer_elem.text else ""
                
                if question and answer:
                    qa_pairs.append({
                        'question': question,
                        'answer': answer
                    })
        
        return qa_pairs
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return []

def load_xml_documents_from_directory(directory_path, max_files=None, specific_dirs=None):
    """
    Load XML documents with options for limiting files and directories
    
    Args:
        directory_path: Path to the root directory
        max_files: Maximum number of files to process (None for all)
        specific_dirs: List of specific subdirectories to process (None for all)
    """
    print("==== Loading XML documents from directory and subdirectories ====")
    documents = []
    total_files = 0
    total_qa_pairs = 0
    processed_files = 0
    
    # Get all XML files
    all_xml_files = []
    for root, dirs, files in os.walk(directory_path):
        # Filter directories if specific_dirs is provided
        if specific_dirs:
            dirs[:] = [d for d in dirs if d in specific_dirs]
        
        for filename in files:
            if filename.endswith(".xml"):
                file_path = os.path.join(root, filename)
                all_xml_files.append(file_path)
    
    print(f"Found {len(all_xml_files)} XML files")
    
    # Limit files if max_files is specified
    if max_files:
        all_xml_files = all_xml_files[:max_files]
        print(f"Processing first {max_files} files for testing")
    
    for file_path in all_xml_files:
        total_files += 1
        processed_files += 1
        
        # Show progress every 10 files
        if processed_files % 10 == 0:
            print(f"Processing file {processed_files}/{len(all_xml_files)}: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                xml_content = file.read()
            
            # Extract QA pairs from XML
            qa_pairs = extract_qa_from_xml(xml_content)
            
            for i, qa in enumerate(qa_pairs):
                # Create a unique ID for each QA pair
                qa_id = f"{os.path.relpath(file_path, directory_path)}_qa_{i+1}"
                
                # Combine question and answer for the document text
                document_text = f"Question: {qa['question']}\nAnswer: {qa['answer']}"
                
                documents.append({
                    "id": qa_id,
                    "text": document_text,
                    "question": qa['question'],
                    "answer": qa['answer'],
                    "source_file": os.path.relpath(file_path, directory_path)
                })
                total_qa_pairs += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"Processed {total_files} XML files")
    print(f"Extracted {total_qa_pairs} QA pairs")
    return documents

def add_documents_to_chroma_batch(documents, collection, batch_size=100):
    """Add documents to ChromaDB collection in batches"""
    print("==== Adding documents to ChromaDB ====")
    
    total_docs = len(documents)
    added_docs = 0
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        
        # Prepare data for ChromaDB
        ids = [doc["id"] for doc in batch]
        texts = [doc["text"] for doc in batch]
        metadatas = [{"question": doc["question"], "answer": doc["answer"], "source_file": doc["source_file"]} for doc in batch]
        
        # Add to collection
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        added_docs += len(batch)
        print(f"Added batch {i//batch_size + 1}: {len(batch)} documents (Total: {added_docs}/{total_docs})")
    
    print(f"Successfully added {added_docs} documents to ChromaDB collection")

def main():
    """Main processing function"""
    global collection  # Declare that we'll modify the global collection variable
    
    print("=== MedQuAD Data Processor ===")
    print("This script will process all XML files and store them in ChromaDB.")
    print("You only need to run this once to create your knowledge base.")
    
    # Configuration
    TEST_MODE = input("Run in test mode? (y/n, default: y): ").lower() != 'n'
    
    if TEST_MODE:
        print("\n=== TEST MODE ===")
        MAX_FILES = int(input("Number of files to process (default: 50): ") or "50")
        SPECIFIC_DIRS = ["1_CancerGov_QA"]  # Start with one directory for testing
        print(f"Processing {MAX_FILES} files from {SPECIFIC_DIRS[0]}")
    else:
        print("\n=== FULL MODE ===")
        MAX_FILES = None
        SPECIFIC_DIRS = None
        print("Processing ALL files from ALL directories")
    
    # Check if collection already has data
    existing_count = collection.count()
    if existing_count > 0:
        print(f"\nCollection already has {existing_count} documents")
        overwrite = input("Do you want to overwrite existing data? (y/n): ").lower() == 'y'
        if overwrite:
            print("Deleting existing collection...")
            chroma_client.delete_collection(collection_name)
            collection = chroma_client.create_collection(name=collection_name)
        else:
            print("Keeping existing data. Exiting.")
            return
    
    # Load documents
    directory_path = "./MedQuAD/"
    start_time = time.time()
    
    documents = load_xml_documents_from_directory(
        directory_path, 
        max_files=MAX_FILES, 
        specific_dirs=SPECIFIC_DIRS
    )
    
    if documents:
        # Add to ChromaDB
        add_documents_to_chroma_batch(documents, collection, batch_size=50)
        
        end_time = time.time()
        print(f"\n=== PROCESSING COMPLETE ===")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Total documents stored: {collection.count()}")
        print(f"\nYou can now use query_medical_qa.py to ask questions!")
    else:
        print("No documents found to process.")

if __name__ == "__main__":
    main() 