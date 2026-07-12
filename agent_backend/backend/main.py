import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from chromadb.utils import embedding_functions
from google import genai
from google.genai import types
import dotenv

dotenv.load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from environment")

client = genai.Client(api_key=api_key)

# Initialize Chroma using local ONNX embeddings
db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = chromadb.PersistentClient(path=db_path)
ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_collection(name="dharma_compass_vast", embedding_function=ef)

class ChatRequest(BaseModel):
    message: str
    language: str = "English"

SYSTEM_PROMPT = """You are Dharma-Compass, a deeply profound philosophical AI representing Indian Knowledge Systems (IKS).
Your goal is to synthesize ancient wisdom to help users with modern dilemmas.
You will be provided with retrieved verses from scriptures (like Bhagavad Gita) related to the user's query.

CRITICAL INSTRUCTIONS:
1. Read the user's dilemma carefully.
2. Read the retrieved verses.
3. Write a profound, modern philosophical answer that synthesizes the wisdom from the verses.
4. **STRICT LENGTH LIMIT**: Your response MUST be concise and punchy. Maximum 2 paragraphs. Do not write a huge essay.
5. Always cite the specific verses in your response (e.g. "As stated in the Bhagavad Gita (2:47)...").
6. **LANGUAGE**: You must respond fluently in the requested language: {language}. Ensure the translation maintains the profound, philosophical tone.

RETRIEVED VERSES:
{context}
"""

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # 1. Retrieve
        results = collection.query(
            query_texts=[req.message],
            n_results=3
        )
        
        retrieved_texts = []
        if results['documents'] and len(results['documents'][0]) > 0:
            retrieved_texts = results['documents'][0]
            
        context = "\n\n".join(retrieved_texts)
        
        # 2. Synthesize
        prompt = SYSTEM_PROMPT.format(context=context, language=req.language)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                f"My dilemma is: {req.message}"
            ]
        )
        
        return {
            "response": response.text,
            "sources": results['metadatas'][0] if results['metadatas'] else []
        }
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg or "400" in error_msg:
            raise HTTPException(status_code=500, detail="Gemini API Key is invalid. Please check your .env file and ensure GEMINI_API_KEY is set correctly.")
        raise HTTPException(status_code=500, detail=error_msg)
