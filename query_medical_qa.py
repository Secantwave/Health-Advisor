"""
Medical QA Query System
This script queries the pre-processed MedQuAD data stored in ChromaDB.
Make sure you've run process_medquad_data.py first to create the knowledge base.
"""

from dotenv import load_dotenv
from google import genai
import chromadb
import os

load_dotenv()

# Setup
gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_key)

# ChromaDB setup
collection_name = "medquad_qa_collection"
chroma_client = chromadb.PersistentClient(path="chroma_persistent_storage")
collection = chroma_client.get_or_create_collection(name=collection_name)

def query_medical_qa(question, collection, client, top_k=5):
    """Query the medical QA collection"""
    print(f"==== Querying: {question} ====")
    
    # Search in ChromaDB
    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )
    
    # Format results for Gemini
    context = "\n\n".join(results['documents'][0])
    
    # Create prompt for Gemini
    prompt = f"""You are a medical assistant. Based on the following medical information, answer the user's question. 
    If the information provided doesn't contain the answer, say so clearly.

    Medical Information:
    {context}

    User Question: {question}

    Please provide a clear, accurate, and helpful answer based on the medical information above."""

    # Query Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    
    return {
        'answer': response.text,
        'sources': results['metadatas'][0],
        'distances': results['distances'][0]
    }

def show_collection_info():
    """Show information about the current collection"""
    count = collection.count()
    print(f"Knowledge base contains {count} medical Q&A pairs")
    
    if count == 0:
        print("\n⚠️  No data found! Please run process_medquad_data.py first.")
        return False
    return True

def interactive_query():
    """Interactive query mode"""
    print("\n=== Medical QA System ===")
    print("Ask medical questions and get answers based on the MedQuAD dataset.")
    print("Type 'quit' to exit.")
    
    while True:
        question = input("\n🤔 Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        try:
            result = query_medical_qa(question, collection, client)
            
            print(f"\n💡 Answer: {result['answer']}")
            print(f"📚 Sources: {len(result['sources'])} relevant documents found")
            
            # Show source information
            if result['sources']:
                print("\n📖 Source documents:")
                for i, source in enumerate(result['sources'], 1):
                    if 'source_file' in source:
                        # MedQuAD source
                        print(f"  {i}. {source['source_file']}")
                        print(f"     Q: {source['question'][:100]}...")
                    elif 'title' in source:
                        # MedlinePlus source
                        print(f"  {i}. {source['title']}")
                        print(f"     Source: {source['source']}")
                        if 'url' in source:
                            print(f"     URL: {source['url']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("=== Medical QA Query System ===")
    
    # Check if we have data
    if not show_collection_info():
        return
    
    # Ask user what they want to do
    print("\nOptions:")
    print("1. Interactive query mode")
    print("2. Single question")
    print("3. Exit")
    
    choice = input("\nChoose an option (1-3): ").strip()
    
    if choice == "1":
        interactive_query()
    elif choice == "2":
        question = input("Enter your medical question: ").strip()
        if question:
            result = query_medical_qa(question, collection, client)
            print(f"\n💡 Answer: {result['answer']}")
            print(f"📚 Sources: {len(result['sources'])} relevant documents found")
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main() 