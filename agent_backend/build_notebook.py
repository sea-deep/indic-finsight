import nbformat as nbf

nb = nbf.v4.new_notebook()

# Cell 1: Intro Markdown
intro_md = """# Indic-FinSight: Multi-Agent Financial Analyst
**Kaggle Submission — Gemma 2B on T4 GPU**

A multi-agent system that breaks complex financial queries into sub-tasks,
delegates to specialized agents (Filings, Market, Chart), and synthesizes
a unified answer.

**Architecture:**
```
User Query → Intent Router → [FilingsAgent | MarketAgent | ChartAgent] → Orchestrator → Response
```
"""

# Cell 2: Installs
installs = """!pip install -q -U chromadb fastembed yfinance transformers accelerate bitsandbytes fastapi uvicorn pydantic nest-asyncio
!npm install -g localtunnel"""

# Cell 3: Imports
imports = """import torch
import chromadb
import yfinance as yf
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import re
import json
import warnings
warnings.filterwarnings('ignore')"""

# Cell 4: RAG Setup
rag_setup = """# 1. Financial Document Ingestion (ChromaDB Vector Store)

dense_financial_text = '''
Reliance Industries Q3 FY26 Earnings Call Transcript Excerpt:
The management recognizes that the global semiconductor shortage continues to pose a supply chain risk, though we expect it to stabilize by Q4.
Commodity inflation, particularly in steel and lithium, has impacted our margin by 120 basis points.
On a positive note, our Retail segment and Jio saw a 45% YoY growth.
We remain committed to our net-zero carbon emission goal by 2040.
Capital expenditure for the upcoming fiscal is slated at 8,000 Crores, largely directed towards 5G expansion.
Revenue for Q3 FY26 stood at Rs 2,40,000 Crores, up 12% YoY.
Net profit for Q3 FY26 was Rs 18,500 Crores, a 15% increase over the previous year.
The O2C segment reported EBITDA of Rs 15,200 Crores with margins at 8.2%.
Jio Platforms added 12 million subscribers this quarter, taking total to 482 million.
Retail segment revenue crossed Rs 75,000 Crores with 3,200 new store openings.
Debt-to-equity ratio improved to 0.32 from 0.38 in the previous quarter.
The company announced a dividend of Rs 10 per share for FY26.
'''

print("Initializing ChromaDB vector store...")
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="financial_filings")

chunks = [chunk.strip() for chunk in dense_financial_text.split('.') if len(chunk.strip()) > 20]

collection.add(
    documents=chunks,
    metadatas=[{"source": "Reliance Industries Q3 FY26 Transcript"} for _ in chunks],
    ids=[str(i) for i in range(len(chunks))]
)
print(f"Ingested {len(chunks)} chunks into vector store.")"""

# Cell 5: Model Loading
model_loading = """# 2. Load Gemma 2B from Kaggle Model Hub
import os
import glob

print("Locating Gemma 2 model weights...")
possible_paths = glob.glob("/kaggle/input/**/config.json", recursive=True)

model_path = None
for p in possible_paths:
    if "gemma" in p.lower():
        model_path = os.path.dirname(p)
        break

if not model_path:
    raise FileNotFoundError("Gemma 2 model not attached. Add it via Kaggle sidebar: Models → Gemma 2 → gemma-2-2b-it.")

print(f"Loading from: {model_path}")

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.float16,
)

gemma = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.1,
)
print("Model loaded.")"""

# Cell 6: Tools
tools_code = """# 3. Tool Definitions

def search_filings(query: str) -> str:
    results = collection.query(query_texts=[query], n_results=3)
    return " ".join(results['documents'][0])

def get_live_stock_price(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker.strip())
        hist = stock.history(period="5d")
        if hist.empty:
            return f"No data found for {ticker}."
        price = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
        change = ((price - prev) / prev) * 100
        direction = "up" if change >= 0 else "down"
        return f"{ticker}: ₹{price:.2f} ({direction} {abs(change):.2f}% from previous close)"
    except Exception as e:
        return f"Error fetching {ticker}: {e}"

def plot_bar_chart(title_and_data: str) -> str:
    return f"[CHART:{title_and_data}]"

TOOLS = {
    "search_filings": search_filings,
    "get_live_stock_price": get_live_stock_price,
    "plot_bar_chart": plot_bar_chart,
}"""

# Cell 7: Multi-Agent System
agent_code = """# 4. Multi-Agent Orchestration System

INTENT_KEYWORDS = {
    "filings": ["risk", "risks", "filing", "report", "earnings", "revenue", "profit",
                "margin", "capex", "growth", "debt", "ebitda", "dividend", "subscriber",
                "supply chain", "segment", "quarter", "annual", "fy", "q1", "q2", "q3", "q4"],
    "market":  ["price", "stock", "ticker", "nse", "bse", "live", "current", "share price",
                "market cap", "trading"],
    "chart":   ["chart", "graph", "plot", "visualize", "bar chart", "trend", "compare"],
}

def classify_intent(query: str) -> list:
    query_lower = query.lower()
    intents = []
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            intents.append(intent)
    if not intents:
        intents = ["filings"]
    return intents

AGENT_PROMPTS = {
    "filings": '''You are FilingsAgent, a financial document analyst.
You have ONE tool: search_filings(query)
Your job: search the company filings database and extract relevant information.

Format your response EXACTLY as:
Thought: [your reasoning]
Action: search_filings
Action Input: [your search query]

After receiving an Observation, provide:
Thought: [analysis of what you found]
Result: [concise summary of findings]''',

    "market": '''You are MarketAgent, a live market data specialist.
You have ONE tool: get_live_stock_price(ticker)
Your job: fetch the current stock price for the requested ticker.

Format your response EXACTLY as:
Thought: [identify the ticker]
Action: get_live_stock_price
Action Input: [TICKER.NS format]

After receiving an Observation, provide:
Thought: [brief analysis]
Result: [the price data]''',

    "chart": '''You are ChartAgent, a data visualization specialist.
You have ONE tool: plot_bar_chart(title_and_data)
The tool input format is: Chart Title | label1=value1, label2=value2, label3=value3

Your job: extract numeric data from the conversation context and create a chart.

Format your response EXACTLY as:
Thought: [identify what data to chart]
Action: plot_bar_chart
Action Input: [Title | key1=val1, key2=val2]

After receiving an Observation, provide:
Thought: [confirm chart created]
Result: [description of the chart]''',
}

def run_sub_agent(agent_type, user_query, context="", max_steps=4):
    agent_prompt = AGENT_PROMPTS[agent_type]
    tool_map = {
        "filings": {"search_filings": search_filings},
        "market": {"get_live_stock_price": get_live_stock_price},
        "chart": {"plot_bar_chart": plot_bar_chart},
    }
    tools = tool_map[agent_type]
    
    system = f"{agent_prompt}\\n\\nContext from other agents: {context}" if context else agent_prompt
    chat = [{"role": "user", "content": f"{system}\\n\\nUser Query: {user_query}"}]
    
    full_trace = []
    
    for step in range(max_steps):
        prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        prompt += "Thought:"
        
        output = gemma(prompt)[0]['generated_text']
        response = "Thought:" + output[len(prompt):]
        
        # Clean up: stop at any second "Thought:" to prevent rambling
        parts = response.split("Thought:")
        if len(parts) > 2:
            response = "Thought:" + parts[1]
        
        full_trace.append({"agent": agent_type, "step": step + 1, "output": response.strip()})
        chat.append({"role": "assistant", "content": response})
        
        # Check for Result (sub-agent is done)
        if "Result:" in response:
            result_match = re.search(r"Result:\\s*(.*)", response, re.DOTALL)
            result = result_match.group(1).strip() if result_match else response
            return {"result": result, "trace": full_trace}
        
        # Parse and execute tool call
        action_match = re.search(r"Action:\\s*(\\S+)", response)
        input_match = re.search(r"Action Input:\\s*(.*)", response)
        
        if action_match and input_match:
            action = action_match.group(1).strip()
            action_input = input_match.group(1).strip()
            
            if action in tools:
                observation = tools[action](action_input)
            else:
                observation = f"Error: Unknown tool {action}. Available: {list(tools.keys())}"
            
            full_trace.append({"agent": agent_type, "step": step + 1, "observation": observation})
            chat.append({"role": "user", "content": f"Observation: {observation}"})
        else:
            chat.append({"role": "user", "content": "You must use the Action/Action Input format, or provide a Result."})
    
    # If we exhausted steps, return whatever we have
    return {"result": "Agent could not complete the task in the allowed steps.", "trace": full_trace}


def run_orchestrator(user_query, previous_history=None):
    print(f"\\n{'='*60}")
    print(f"QUERY: {user_query}")
    print(f"{'='*60}")
    
    # Step 1: Classify intent
    intents = classify_intent(user_query)
    print(f"Intents detected: {intents}")
    
    # Step 2: Run sub-agents
    agent_results = {}
    all_traces = []
    context = ""
    
    for intent in intents:
        print(f"\\n--- Dispatching to {intent.upper()} agent ---")
        result = run_sub_agent(intent, user_query, context=context)
        agent_results[intent] = result["result"]
        all_traces.extend(result["trace"])
        context += f" {result['result']}"
        print(f"[{intent.upper()}] Result: {result['result']}")
    
    # Step 3: Synthesize final answer
    synthesis_prompt = f'''You are a financial analyst. Combine these agent reports into one clear, professional response.

User asked: {user_query}

Agent Reports:
'''
    for agent_type, result in agent_results.items():
        synthesis_prompt += f"- {agent_type.title()} Agent: {result}\\n"
    
    synthesis_prompt += "\\nProvide a comprehensive answer. Be specific with numbers. Do not say you lack data if agents provided it."
    
    chat = [{"role": "user", "content": synthesis_prompt}]
    prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    output = gemma(prompt)[0]['generated_text']
    final_answer = output[len(prompt):].strip()
    
    print(f"\\nFINAL ANSWER: {final_answer}")
    
    # Build response for frontend
    trace_text = ""
    for t in all_traces:
        if 'output' in t:
            trace_text += f"{t['output']}\\n"
        if 'observation' in t:
            trace_text += f"Observation: {t['observation']}\\n"
    
    combined = trace_text + f"Final Answer: {final_answer}"
    
    return [
        {"role": "assistant", "content": combined, "agents_used": intents}
    ]"""

# Cell 8: Test execution
execution_code = """# 5. Test Run
result = run_orchestrator("What are the supply chain risks for Reliance Industries, and what is their live stock price (ticker: RELIANCE.NS)?")
for msg in result:
    print(msg["content"])"""

# Cell 9: API Server
api_code = """# 6. FastAPI Server + Localtunnel
import nest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import subprocess
import threading
import time

app = FastAPI(title="Indic-FinSight API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    text: str
    history: list = []

@app.get("/health")
def health():
    return {"status": "ok", "model": "gemma-2-2b-it", "agents": ["filings", "market", "chart"]}

@app.post("/chat")
def chat(query: Query):
    result = run_orchestrator(query.text, previous_history=query.history)
    return {"history": result}

def run_server():
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)

print("Starting API server...")
threading.Thread(target=run_server, daemon=True).start()
time.sleep(3)

SUBDOMAIN = "indic-finsight-seaadeep-998877"
print(f"Starting tunnel...")
lt = subprocess.Popen(["lt", "--port", "8000", "--subdomain", SUBDOMAIN], stdout=subprocess.PIPE)
print(f"\\n{'='*60}")
print(f"API LIVE: https://{SUBDOMAIN}.loca.lt")
print(f"{'='*60}")

for line in lt.stdout:
    decoded = line.decode('utf-8').strip()
    if "your url is" in decoded.lower():
        print(decoded)
        break

import asyncio
async def keep_alive():
    while True:
        await asyncio.sleep(3600)

await keep_alive()"""


nb['cells'] = [
    nbf.v4.new_markdown_cell(intro_md),
    nbf.v4.new_code_cell(installs),
    nbf.v4.new_code_cell(imports),
    nbf.v4.new_code_cell(rag_setup),
    nbf.v4.new_code_cell(model_loading),
    nbf.v4.new_code_cell(tools_code),
    nbf.v4.new_code_cell(agent_code),
    nbf.v4.new_code_cell(execution_code),
    nbf.v4.new_code_cell(api_code),
]

nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}

with open('/home/dipak/code/kaggle-hackathon/agent_backend/kaggle_submission/notebook.ipynb', 'w') as f:
    nbf.write(nb, f)
print("Notebook generated successfully.")
