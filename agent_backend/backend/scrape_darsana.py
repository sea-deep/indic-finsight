import chromadb
import uuid
import requests
import re
from fastembed import TextEmbedding

print("Initializing ChromaDB and FastEmbed...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
collection = chroma_client.get_or_create_collection(name="dharma_compass")

# The Universal Taxonomy of Darśana mapping Wikipedia page titles to their Philosophy
taxonomy = {
    # Astika - Vedic Foundation
    "Rigveda": "Vedic Foundation",
    "Yajurveda": "Vedic Foundation",
    "Samaveda": "Vedic Foundation",
    "Atharvaveda": "Vedic Foundation",
    "Upanishads": "Vedic Foundation",
    "Brahma_Sutras": "Vedic Foundation",
    
    # Astika - Nyaya (Logic)
    "Nyaya": "Āstika - Nyāya",
    "Nyāya_Sūtras": "Āstika - Nyāya",
    "Tattvacintāmaṇi": "Āstika - Nyāya",
    
    # Astika - Vaisesika (Atomism)
    "Vaisheshika": "Āstika - Vaiśeṣika",
    "Vaiśeṣika_Sūtra": "Āstika - Vaiśeṣika",
    
    # Astika - Sankhya (Dualism)
    "Samkhya": "Āstika - Sāṅkhya",
    "Samkhyakarika": "Āstika - Sāṅkhya",
    
    # Astika - Yoga
    "Yoga_Sutras_of_Patanjali": "Āstika - Yoga",
    "Hatha_Yoga_Pradipika": "Āstika - Yoga",
    
    # Astika - Purva Mimamsa
    "Mimamsa": "Āstika - Pūrva Mīmāṃsā",
    "Mimamsa_Sutras": "Āstika - Pūrva Mīmāṃsā",
    
    # Astika - Vedanta
    "Vedanta": "Āstika - Vedānta",
    "Advaita_Vedanta": "Āstika - Advaita",
    "Vishishtadvaita": "Āstika - Viśiṣṭādvaita",
    "Dvaita_Vedanta": "Āstika - Dvaita",
    "Achintya_Bheda_Abheda": "Āstika - Acintya Bhedābheda",
    
    # Nastika - Buddhism
    "Buddhist_philosophy": "Nāstika - Buddhism",
    "Tripiṭaka": "Nāstika - Buddhism",
    "Lotus_Sutra": "Nāstika - Buddhism",
    "Heart_Sutra": "Nāstika - Buddhism",
    "Diamond_Sutra": "Nāstika - Buddhism",
    "Madhyamaka": "Nāstika - Buddhism",
    "Yogachara": "Nāstika - Buddhism",
    
    # Nastika - Jainism
    "Jain_philosophy": "Nāstika - Jainism",
    "Jain_Agamas": "Nāstika - Jainism",
    "Tattvartha_Sutra": "Nāstika - Jainism",
    
    # Nastika - Carvaka
    "Charvaka": "Nāstika - Cārvāka",
    
    # Nastika - Ajivika / Ajnana
    "Ājīvika": "Nāstika - Ājīvika",
    "Ajnana": "Nāstika - Ajñāna"
}

headers = {'User-Agent': 'DharmaCompassBot/1.0 (dipak@example.com)'}

def clean_text(text):
    text = re.sub(r'\[\d+\]', '', text) # Remove citations
    text = text.replace('\n\n', '\n')
    return text.strip()

print(f"Scraping {len(taxonomy)} sources from Wikipedia...")

documents = []
metadatas = []
ids = []

for wiki_title, philosophy in taxonomy.items():
    print(f"Fetching {wiki_title}...")
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={wiki_title}&format=json"
        res = requests.get(url, headers=headers)
        data = res.json()
        pages = data.get("query", {}).get("pages", {})
        
        for page_id, page_info in pages.items():
            if page_id == "-1":
                print(f"  -> Not found!")
                continue
                
            extract = page_info.get("extract", "")
            if not extract:
                continue
                
            extract = clean_text(extract)
            
            # Chunk by paragraphs to keep embeddings relevant
            paragraphs = [p.strip() for p in extract.split('\n') if len(p.strip()) > 100]
            
            # Limit to top 15 paragraphs per school to avoid overwhelming the DB with pure history
            for i, p in enumerate(paragraphs[:15]):
                source_name = wiki_title.replace("_", " ")
                
                documents.append(p)
                metadatas.append({
                    "source": source_name,
                    "philosophy": philosophy
                })
                ids.append(str(uuid.uuid4()))
                
        print(f"  -> Success! Chunked {wiki_title}")
    except Exception as e:
        print(f"  -> Error fetching {wiki_title}: {e}")

print(f"Embedding {len(documents)} newly scraped philosophical chunks...")
embeddings_gen = list(embedding_model.embed(documents))
embeddings = [e.tolist() for e in embeddings_gen]

print("Saving to ChromaDB...")
batch_size = 100
for i in range(0, len(documents), batch_size):
    collection.add(
        documents=documents[i:i+batch_size],
        metadatas=metadatas[i:i+batch_size],
        embeddings=embeddings[i:i+batch_size],
        ids=ids[i:i+batch_size]
    )

print("SUCCESS: Darśana Expansion Complete! The RAG now contains all major schools of Indian Philosophy.")
