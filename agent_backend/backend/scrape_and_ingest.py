import os
import json
import glob
import chromadb
from chromadb.utils import embedding_functions

def ingest_gita():
    print("Initializing ChromaDB...")
    db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Use Chroma's default ONNX embedding function (No PyTorch required, runs locally on CPU)
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    # Create or get collection
    try:
        client.delete_collection("dharma_compass_vast")
    except Exception:
        pass
        
    collection = client.create_collection(
        name="dharma_compass_vast",
        embedding_function=ef
    )
    
    # Path to DharmicData Gita JSONs
    gita_path = "/tmp/DharmicData/SrimadBhagvadGita/*.json"
    files = glob.glob(gita_path)
    
    if not files:
        print(f"Error: No files found at {gita_path}")
        return
        
    documents = []
    metadatas = []
    ids = []
    
    print("Parsing Srimad Bhagavad Gita JSON files...")
    verse_count = 0
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chapter_data = data.get('BhagavadGitaChapter', [])
            
            for item in chapter_data:
                chapter = item.get('chapter')
                verse = item.get('verse')
                sanskrit_text = item.get('text', '')
                
                # We extract the English translation to embed, so semantic search works for English queries.
                translations = item.get('translations', {})
                # Use Swami Sivananda's translation or any available
                english_translation = translations.get('swami sivananda') or translations.get('shri purohit swami') or ""
                
                if not english_translation:
                    continue
                    
                doc_text = f"Bhagavad Gita {chapter}:{verse} - {english_translation}"
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "Bhagavad Gita",
                    "chapter": chapter,
                    "verse": verse,
                    "sanskrit": sanskrit_text
                })
                ids.append(f"bg_{chapter}_{verse}")
                verse_count += 1

    print(f"Ingesting {verse_count} verses into ChromaDB using local ONNX Embeddings...")
    
    # Batch ingestion (Chroma handles batching nicely)
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"Ingested {min(i+batch_size, len(documents))} / {len(documents)}")
        
    print("Vast Dataset Ingestion Complete! 🕉️")

if __name__ == "__main__":
    ingest_gita()
