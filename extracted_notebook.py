
# CELL 1
!pip install -q -U chromadb fastembed yfinance transformers accelerate bitsandbytes fastapi uvicorn pydantic nest-asyncio duckduckgo-search beautifulsoup4 requests numexpr > /dev/null 2>&1
!npm install -g localtunnel > /dev/null 2>&1

# CELL 2
import torch
import gc
import chromadb
import yfinance as yf
from transformers import AutoProcessor, AutoModelForCausalLM, pipeline
import re
import json
import warnings
import os
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
import requests
import requests
from bs4 import BeautifulSoup
import numexpr
warnings.filterwarnings('ignore')

# CELL 3
# 1. Financial Document Ingestion (ChromaDB Vector Store)

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
print(f"Ingested {len(chunks)} chunks into vector store.")

# CELL 4
# 2. Load Gemma Models from Kaggle Model Hub
import os
import glob
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

print("Locating Gemma 4 model weights...")
possible_paths = glob.glob("/kaggle/input/**/config.json", recursive=True)

path_small = None
path_large = None

for p in possible_paths:
    d = os.path.dirname(p)
    if "e2b" in d.lower():
        path_small = d
    elif "12b" in d.lower() and "assistant" not in d.lower():
        path_large = d

if not path_small or not path_large:
    raise FileNotFoundError("Both Gemma models not attached. Ensure 12B and E2B are attached.")

print(f"Loading Model from: {path_small}")

gc.collect()
torch.cuda.empty_cache()

processor_large = AutoTokenizer.from_pretrained(path_small, padding_side="left")
model_large = AutoModelForCausalLM.from_pretrained(
    path_small,
    device_map="auto",
    torch_dtype=torch.float16,
)
print("Model loaded.")

gemma_chat_template = "{% if messages[0]['role'] == 'system' %}{% set loop_messages = messages[1:] %}{% set system_message = messages[0]['content'] %}{% else %}{% set loop_messages = messages %}{% set system_message = '' %}{% endif %}{% if system_message != '' %}{{ '<start_of_turn>user\n' + system_message + '<end_of_turn>\n<start_of_turn>model\nOk<end_of_turn>\n' }}{% endif %}{% for message in loop_messages %}{% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}{{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}{% endif %}{% if message['role'] == 'user' %}{{ '<start_of_turn>user\n' + message['content'] + '<end_of_turn>\n' }}{% elif message['role'] == 'assistant' %}{{ '<start_of_turn>model\n' + message['content'] + '<end_of_turn>\n' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<start_of_turn>model\n' }}{% endif %}"

processor_large.chat_template = gemma_chat_template

print("Model ready.")

# CELL 5
# 3. Tool Definitions

def search_filings(query: str) -> str:
    results = collection.query(query_texts=[query], n_results=3)
    return " ".join(results['documents'][0])

def get_live_stock_price(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker.strip())
        hist = stock.history(period="5d")
        if hist is None or len(hist) == 0:
            # Fallback to Google Finance
            gf_data = get_google_finance_data(ticker)
            if "N/A" in gf_data:
                return f"No data found for {ticker} via YFinance or Google Finance. Try using web search."
            return gf_data
        price = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
        change = ((price - prev) / prev) * 100 if prev else 0
        direction = "up" if change >= 0 else "down"
        return f"{ticker}: ₹{price:.2f} ({direction} {abs(change):.2f}% from previous close)"
    except Exception as e:
        # Fallback to Google Finance on exception
        gf_data = get_google_finance_data(ticker)
        if "N/A" not in gf_data and "Error" not in gf_data:
            return gf_data
        return f"Error fetching {ticker}: {e}. Try using web search."

def search_web(query: str) -> str:
    try:
        import wikipedia
        # Search for the top matching page
        search_results = wikipedia.search(query, results=1)
        if not search_results:
            return "No web results found."
        
        page = wikipedia.page(search_results[0], auto_suggest=False)
        summary = page.summary
        
        # Truncate summary to avoid context limit issues
        if len(summary) > 1000:
            summary = summary[:1000] + "..."
            
        return f"[{page.title}] {summary}"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Query is too ambiguous. Try being more specific. Options: {e.options[:3]}"
    except Exception as e:
        return f"Web search currently unavailable. Try another query."

def calculate_math(expression: str) -> str:
    try:
        # Secure math evaluation using numexpr
        result = numexpr.evaluate(expression)
        return f"Result: {result.item()}"
    except Exception as e:
        return f"Math error: {e}. Ensure expression is valid math (e.g. '2 + 2')."

def summarize_text(text: str) -> str:
    # A dummy tool for now since the LLM itself can summarize if passed text, 
    # but the agent can use this to explicitly request a summary.
    return f"Summary requested for text length {len(text)}. The agent should read the context."

def plot_chart(type_title_data: str) -> str:
    return f"[CHART:{type_title_data}]"

def get_google_finance_data(ticker: str) -> str:
    try:
        url = f"https://www.google.com/finance/quote/{ticker}:NSE"
        headers = {'User-Agent': 'Mozilla/5.0'}
        import requests
        from bs4 import BeautifulSoup
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_div = soup.find('div', class_='YMlKec fxKbKc')
        price = price_div.text if price_div else "N/A"
        
        about_div = soup.find('div', class_='bLLb2d')
        about = about_div.text if about_div else "N/A"
        
        news_divs = soup.find_all('div', class_='Yfwt5')
        news = [n.text for n in news_divs[:3]]
        
        return f"Google Finance Data for {ticker}:\nPrice: {price}\nAbout: {about}\nRecent News: {', '.join(news)}"
    except Exception as e:
        return f"Error fetching from Google Finance: {str(e)}"

TOOLS = {
    "search_filings": search_filings,
    "get_live_stock_price": get_live_stock_price,
    "get_google_finance_data": get_google_finance_data,
    "search_web": search_web,
    "plot_chart": plot_chart,
    "calculate_math": calculate_math,
    "summarize_text": summarize_text,
}

# CELL 6
# 4. Multi-Agent Orchestration System
import re
import json

INTENT_KEYWORDS = {
    "filings": ["risk", "risks", "filing", "report", "earnings", "revenue", "profit",
                "margin", "capex", "growth", "debt", "ebitda", "dividend", "subscriber",
                "supply chain", "segment", "quarter", "annual", "fy", "q1", "q2", "q3", "q4"],
    "market":  ["price", "stock", "ticker", "nse", "bse", "live", "current", "share price",
                "market cap", "trading"],
    "chart":   ["chart", "graph", "plot", "visualize", "bar chart", "trend", "compare", "pie", "line"],
    "web":     ["news", "recent", "search", "update", "latest", "internet", "web"],
    "math":    ["calculate", "math", "add", "subtract", "multiply", "divide", "sum", "percent"],
    "summary": ["summarize", "summary", "tldr", "shorten"],
}

def classify_intent(query: str) -> list:
    query_lower = query.lower()
    intents = []
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            intents.append(intent)
    if not intents:
        intents = ["web"]  # Default
    return intents

AGENT_PROMPTS = {
    "filings": '''You are FilingsAgent, a financial document analyst.
You have ONE tool: search_filings(query)
Your job: search the company filings database and extract relevant information.

CRITICAL INSTRUCTIONS:
- You MUST respond with a strict JSON block exactly like this:
```json
{
  "thought": "I need to search the filings for this information.",
  "tool": "search_filings",
  "arguments": {"query": "your search query"}
}
```
- If you have finished and found the answer, output:
```json
{
  "thought": "I found the answer.",
  "result": "concise summary of findings"
}
```''',
    "market": r'''You are MarketAgent, a live market data specialist.
You have TWO tools:
1. get_live_stock_price(ticker) - Uses yfinance for live price.
2. get_google_finance_data(ticker) - Uses Google Finance for price, company info, and news.

CRITICAL INSTRUCTIONS:
- NEVER HALLUCINATE TOOL NAMES.
- For get_live_stock_price, append .NS to Indian stock tickers (e.g. RELIANCE.NS)
- For get_google_finance_data, DO NOT append .NS (e.g. RELIANCE)
- You MUST respond with a strict JSON block exactly like this:
```json
{
  "thought": "I need to get the stock price.",
  "tool": "get_live_stock_price",
  "arguments": {"ticker": "RELIANCE.NS"}
}
```
- If you have finished, output:
```json
{
  "thought": "I got the price.",
  "result": "the price data"
}
```''',
    "web": r'''You are WebAgent, a live internet search specialist.
You have ONE tool: search_web(query)
Your job: search the internet for the most recent news or financial information.

CRITICAL INSTRUCTIONS:
- You MUST respond with a strict JSON block exactly like this:
```json
{
  "thought": "I should search the web for this.",
  "tool": "search_web",
  "arguments": {"query": "your search query"}
}
```
- If you have finished, output:
```json
{
  "thought": "I finished the search.",
  "result": "concise summary of findings"
}
```''',
    "chart": '''You are ChartAgent, a data visualization specialist.
You have ONE tool: plot_chart(type_title_data)
The tool input format MUST be: TYPE | Chart Title | label1=value1, label2=value2
TYPE must be one of: bar, line, pie

Your job: extract numeric data from the conversation context and create a chart.

CRITICAL INSTRUCTIONS:
- You MUST respond with a strict JSON block exactly like this:
```json
{
  "thought": "I need to plot this data.",
  "tool": "plot_chart",
  "arguments": {"type_title_data": "bar | Title | key1=val1, key2=val2"}
}
```
- If you have finished, output:
```json
{
  "thought": "Chart created.",
  "result": "description of the chart"
}
```''',
    "math": '''You are MathAgent, a calculation specialist.
You have ONE tool: calculate_math(expression)
Your job: evaluate mathematical expressions.

CRITICAL INSTRUCTIONS:
- You MUST respond with a strict JSON block exactly like this:
```json
{
  "thought": "I need to calculate this.",
  "tool": "calculate_math",
  "arguments": {"expression": "2 + 2"}
}
```
- If you have finished, output:
```json
{
  "thought": "Calculation done.",
  "result": "the final number"
}
```''',
    "summary": '''You are SummaryAgent, a distillation specialist.
You have ONE tool: summarize_text(text)
Your job: summarize long documents.

CRITICAL INSTRUCTIONS:
- You MUST respond with a strict JSON block exactly like this:
```json
{
  "thought": "I need to summarize this.",
  "tool": "summarize_text",
  "arguments": {"text": "long text here"}
}
```
- If you have finished, output:
```json
{
  "thought": "Summary generated.",
  "result": "the summary"
}
```'''
}

def generate_with_keepalive(model, inputs, max_new_tokens):
    import threading
    result_container = []
    def _gen_thread():
        try:
            out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.1, max_length=None)
            result_container.append(out)
        except Exception as e:
            result_container.append(e)
            
    t = threading.Thread(target=_gen_thread)
    t.start()
    while t.is_alive():
        yield {"type": "ping"}
        t.join(timeout=2.0)
        
    if not result_container:
        raise Exception("Generation thread exited without result")
    if isinstance(result_container[0], Exception):
        raise result_container[0]
    yield result_container[0]

def run_sub_agent(agent_type, user_query, context="", max_steps=4, previous_history=None):
    agent_prompt = AGENT_PROMPTS[agent_type]
    tool_map = {
        "filings": {"search_filings": search_filings},
        "market": {"get_live_stock_price": get_live_stock_price, "get_google_finance_data": get_google_finance_data},
        "web": {"search_web": search_web},
        "chart": {"plot_chart": plot_chart},
        "math": {"calculate_math": calculate_math},
        "summary": {"summarize_text": summarize_text},
    }
    tools = tool_map.get(agent_type, {})
    
    # Single model — use tight token limits since outputs are small JSON
    model_curr = model_large
    processor_curr = processor_large
    
    if agent_type in ["chart"]:
        max_new = 384
    else:
        max_new = 192
    
    system = f"{agent_prompt}\n\nContext from other agents: {context}" if context else agent_prompt
    if previous_history and len(previous_history) > 1:
        chat = []
        for i, msg in enumerate(previous_history[:-1]):
            role = msg["role"]
            content = str(msg.get("content", ""))
            if i == 0 and role == "user":
                content = f"{system}\n\n{content}"
            chat.append({"role": role, "content": content})
        chat.append({"role": "user", "content": f"User Query: {user_query}"})
    else:
        chat = [{"role": "user", "content": f"{system}\n\nUser Query: {user_query}"}]
    
    for step in range(max_steps):
        inputs = processor_curr.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True).to(model_curr.device)
        output_ids = None
        for item in generate_with_keepalive(model_curr, inputs, max_new):
            if isinstance(item, dict) and item.get("type") == "ping":
                yield item
            else:
                output_ids = item
                break
        # Decode only the newly generated tokens
        new_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
        response = processor_curr.decode(new_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False).strip()
        
        chat.append({"role": "assistant", "content": response})
        
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                yield {"type": "step", "agent": agent_type, "step": step+1, "thought": parsed.get("thought", ""), "tool": parsed.get("tool"), "arguments": parsed.get("arguments")}
                
                if "result" in parsed:
                    yield {"type": "result", "agent": agent_type, "result": parsed["result"]}
                    return
                
                tool_name = parsed.get("tool")
                args = parsed.get("arguments", {})
                if tool_name in tools:
                    if isinstance(args, str):
                        arg_val = args
                    elif isinstance(args, dict):
                        arg_val = list(args.values())[0] if args else ""
                    else:
                        arg_val = str(args)
                    observation = tools[tool_name](arg_val)
                else:
                    observation = f"Error: Unknown tool {tool_name}."
                
                yield {"type": "observation", "agent": agent_type, "observation": observation}
                chat.append({"role": "user", "content": f"Observation: {observation}"})
                
            except json.JSONDecodeError:
                yield {"type": "error", "agent": agent_type, "error": "Invalid JSON format"}
                chat.append({"role": "user", "content": "Your JSON was invalid. Please output a valid JSON block."})
        else:
            yield {"type": "error", "agent": agent_type, "error": "No JSON block found"}
            chat.append({"role": "user", "content": "You must use the ```json format."})
            
    yield {"type": "result", "agent": agent_type, "result": "Agent could not complete task."}

def run_orchestrator(user_query, previous_history=None):
    yield {"type": "info", "message": f"ORCHESTRATOR AWAKE. Analyzing query: {user_query}"}
    
    system_prompt = '''You are the Conscious Orchestrator, the central intelligence of the Indic-FinSight financial system. 
You are fully aware of your capabilities and the tools at your disposal. Your job is to deeply understand the user's intent, break down complex queries into steps, and delegate tasks to your specialized sub-agents. You must synthesize the final answer based on what the sub-agents discover.

Available Sub-Agents:
- filings: Analyzes SEC/NSE filings, earnings transcripts, and annual reports.
- market: Fetches live stock prices and Yahoo Finance data.
- chart: Generates plotting data for visualization.
- web: Searches the open internet for news or info not in the local database.
- math: Performs exact numerical calculations.

CRITICAL INSTRUCTIONS:
- You MUST respond with a strict JSON block exactly like this to delegate to a sub-agent:
```json
{
  "thought": "I need to check the filings for supply chain risks.",
  "tool": "delegate",
  "agent": "filings",
  "query": "What are the supply chain risks?"
}
```
- If you have gathered all necessary information from the sub-agents, or if you can answer the question directly, output exactly this format to conclude:
```json
{
  "thought": "I have enough information. I will synthesize the final response.",
  "final_answer": "The comprehensive response formatted in markdown..."
}
```
- Format your final answer using bolding, lists, and proper spacing. If data was missing, suggest 2 or 3 follow-up queries at the very end in the format: [OPTIONS: Option 1 | Option 2]'''

    chat = []
    if previous_history and len(previous_history) > 1:
        for i, msg in enumerate(previous_history[:-1]):
            role = msg["role"]
            content = str(msg.get("content", ""))
            if i == 0 and role == "user":
                content = f"{system_prompt}\n\n{content}"
            chat.append({"role": role, "content": content})
        chat.append({"role": "user", "content": f"User Query: {user_query}"})
    else:
        chat = [{"role": "user", "content": f"{system_prompt}\n\nUser Query: {user_query}"}]
        
    agents_used = []
    
    for step in range(8): # Limit to 8 steps to prevent absolute infinite loops, but large enough for most tasks
        inputs = processor_large.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True).to(model_large.device)
        output_ids = None
        for item in generate_with_keepalive(model_large, inputs, 256):
            if isinstance(item, dict) and item.get("type") == "ping":
                yield item
            else:
                output_ids = item
                break
        new_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
        response = processor_large.decode(new_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False).strip()
        
        chat.append({"role": "assistant", "content": response})
        
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                yield {"type": "info", "message": f"Orchestrator Thought: {parsed.get('thought', 'Thinking...')}"}
                
                if "final_answer" in parsed:
                    final_answer_raw = parsed["final_answer"]
                    options = []
                    options_match = re.search(r'\[([^\]]*?\|[^\]]*?)\]', final_answer_raw, re.IGNORECASE | re.DOTALL)
                    if options_match:
                        options_text = options_match.group(1)
                        parts = [p.strip() for p in options_text.split('|')]
                        for p in parts:
                            clean = p.strip('"\\\'').strip()
                            if clean: options.append(clean)
                        final_answer = re.sub(r'\[([^\]]*?\|[^\]]*?)\]', '', final_answer_raw, flags=re.IGNORECASE | re.DOTALL).strip()
                    else:
                        final_answer = final_answer_raw
                    
                    yield {"type": "final_answer", "content": final_answer, "options": options, "agents_used": list(set(agents_used))}
                    return
                
                if parsed.get("tool") == "delegate":
                    target_agent = parsed.get("agent")
                    agent_query = parsed.get("query", "")
                    
                    yield {"type": "info", "message": f"Orchestrator delegating to {target_agent.upper()} Agent..."}
                    agents_used.append(target_agent)
                    
                    sub_agent_generator = run_sub_agent(target_agent, agent_query, context="", max_steps=4)
                    last_result = ""
                    for chunk in sub_agent_generator:
                        if chunk["type"] == "result":
                            last_result = chunk["result"]
                        yield chunk
                        
                    chat.append({"role": "user", "content": f"Sub-Agent '{target_agent}' returned: {last_result}"})
                else:
                    chat.append({"role": "user", "content": "Error: Unknown tool. Only 'delegate' or 'final_answer' are permitted."})
            except json.JSONDecodeError:
                chat.append({"role": "user", "content": "Your JSON was invalid. Please output a valid JSON block."})
        else:
            chat.append({"role": "user", "content": "You must use the ```json format. Please try again."})
            
    yield {"type": "final_answer", "content": "Orchestrator reached maximum loop limit.", "options": [], "agents_used": agents_used}


# CELL 7
# 5. Test Run
# Streaming responses in standard kaggle output omitted


# CELL 8
# 6. FastAPI Server + Localtunnel
import nest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import subprocess
import threading
import time
from fastapi.responses import StreamingResponse
import json

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
def health_check():
    return {"status": "ok", "model": "gemma-4-hybrid", "agents": ["filings", "market", "chart", "web", "math", "summary"]}

@app.post("/chat")
def chat(query: Query):
    def event_stream():
        try:
            for chunk in run_orchestrator(query.text, previous_history=query.history):
                # SSE format
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': f'Server Error: {str(e)}'})}\n\n"
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")

def run_server():
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)

print("Starting API server...")
threading.Thread(target=run_server, daemon=True).start()
time.sleep(3)

SUBDOMAIN = "indic-finsight-seaadeep-998877"
print(f"Starting tunnel...")
lt = subprocess.Popen(["lt", "--port", "8000", "--subdomain", SUBDOMAIN], stdout=subprocess.PIPE)
print(f"\n{'='*60}")
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

await keep_alive()
