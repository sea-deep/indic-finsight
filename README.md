# Indic-FinSight

**Indic-FinSight** is an advanced, multi-agent autonomous financial analyst. It is designed to tackle the fragmented nature of financial research by unifying document analysis, live market tracking, and dynamic data visualization into a single, cohesive chat interface.

## The Problem
Financial research is often tedious and disjointed. Analysts must manually comb through dense earnings transcripts and SEBI/SEC filings for insights, separately monitor live stock prices across different platforms, and manually compile data into charts to identify trends. This constant context-switching slows down decision-making and increases the risk of missing critical information.

## The Solution
Indic-FinSight solves this by introducing a **Multi-Agent AI Architecture**. Instead of relying on a single monolithic language model that might hallucinate or fail at specialized tasks, Indic-FinSight routes your query to a team of specialized sub-agents:

- **FilingsAgent**: Performs RAG-based semantic search over dense financial filings (e.g., earnings call transcripts, SEBI documents) using ChromaDB to extract deep, factual insights.
- **MarketAgent**: Integrates with live market feeds (via `yfinance` and Google Finance) to fetch up-to-date ticker information, current prices, and recent news.
- **ChartAgent**: Dynamically extracts numerical data and structures it into bar, line, or pie charts that are rendered directly in the UI.
- **WebAgent**: Scours the open internet for the latest news and updates not present in local databases.
- **MathAgent & SummaryAgent**: Handle precise numerical calculations and document distillation.

An **Intent Router** automatically classifies incoming queries and dispatches them to the right agent. Finally, an **Orchestrator** agent synthesizes the findings from the sub-agents into a unified, actionable response.

## Features

- **True Multi-Agent Routing**: Queries are autonomously broken down and assigned to specialized agents with focused prompts and tools.
- **Live Data & RAG Integration**: Combines the precision of ChromaDB semantic search for historical data with live market endpoints for real-time accuracy.
- **Dynamic Chart Generation**: Automatically visualizes trends and segment revenues directly in the chat window.
- **Sleek Business UI**: Built with React, TailwindCSS, Recharts, and Lucide Icons, featuring an elegant dark mode designed for professional financial applications.
- **Privacy First**: Designed so that inference can run entirely within a private, secure compute environment. No sensitive financial queries need to be sent to external, closed-source APIs.

## Project Structure

- `frontend/`: The React web application providing the sleek user interface.
- `agent_backend/`: The multi-agent orchestrator logic and API backend.
  - `build_notebook.py`: Generates the backend environment setup and execution script (`notebook.ipynb`) which can be deployed to GPU-accelerated cloud environments.

## How It Works

1. **User Query**: You enter a natural language query via the React frontend.
2. **Intent Routing**: The backend classifies the query and routes it to one or more specialized sub-agents.
3. **Agent Action**: The sub-agent takes over, determines the necessary tool (e.g., `search_filings`, `get_live_stock_price`, `plot_chart`), formulates an action, and executes it.
4. **Orchestration**: The main Orchestrator synthesizes the findings and observations from the sub-agents.
5. **UI Rendering**: The frontend displays the analytical steps taken by the agents in real-time, followed by the final synthesized answer and any relevant interactive charts.

## Deployment

The backend is intended to run in a Jupyter Notebook environment (e.g., JupyterLab) equipped with a T4 GPU (or similar) for fast inference. It uses `localtunnel` to expose a FastAPI endpoint to the public internet, which the frontend consumes.

### 1. Backend
1. Generate the deployment notebook locally:
   ```bash
   python agent_backend/build_notebook.py
   ```
2. Upload the generated `agent_backend/kaggle_submission/notebook.ipynb` to your preferred GPU-enabled notebook environment and execute all cells.
3. Once the environment boots and the script runs, the FastAPI server will automatically host itself on Localtunnel.

### 2. Frontend
Run the React application locally:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## API Testing

You can test the API directly using `cURL`. Make sure you pass the `Bypass-Tunnel-Reminder` header for Localtunnel if applicable.

```bash
curl -X POST https://indic-finsight-seaadeep-998877.loca.lt/chat \
  -H "Content-Type: application/json" \
  -H "Bypass-Tunnel-Reminder: true" \
  -d '{"text": "Show a chart of Reliance segment revenues", "history": []}'
```

Expected output includes the multi-agent reasoning trace (Thought, Action, Result) in Server-Sent Events (SSE) format, culminating in a synthesized `Final Answer`.
