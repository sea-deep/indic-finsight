# Indic-FinSight

**Indic-FinSight** is a multi-agent financial analyst built for the Kaggle Gemma 2B Hackathon. It utilizes a true multi-agent system powered by the **Gemma-2-2b-it** model running on Kaggle's free T4 GPUs.

## Features

- **RAG Retrieval**: Semantic search over financial filings (e.g., earnings call transcripts) using ChromaDB.
- **Live Market Data**: Integrates with Yahoo Finance (`yfinance`) for up-to-date ticker information.
- **Chart Generation**: Dynamically constructs structured bar chart data parsed directly by the UI.
- **Intent Router**: Automatically classifies incoming queries and dispatches them to specialized sub-agents:
  - `FilingsAgent`: Extracts deep financial insights.
  - `MarketAgent`: Fetches live market trends and stock data.
  - `ChartAgent`: Formats data for visual consumption.
- **Sleek Business UI**: Built with React, TailwindCSS, and Lucide Icons, featuring an elegant dark mode designed for professional financial applications.

## Project Structure

- `frontend/`: The React web application.
- `agent_backend/`: The multi-agent orchestrator and Kaggle submission script.
  - `build_notebook.py`: Generates the `notebook.ipynb` file that is submitted to Kaggle.

## How It Works

1. **User Query**: You enter a query via the React frontend.
2. **Intent Routing**: The backend classifies the query and routes it to one or more sub-agents.
3. **Agent Action**: The specialized agent takes over. It determines the necessary tool (e.g., `search_filings`, `get_live_stock_price`, `plot_bar_chart`), formulates an action, and executes it.
4. **Orchestration**: The main Orchestrator synthesizes the findings from the sub-agents.
5. **UI Rendering**: The frontend displays the analytical steps taken by the agents, followed by the final answer and any relevant charts.

## Deployment

The backend is intended to run as a Kaggle Notebook (to leverage the T4 GPU). It uses `localtunnel` to expose a FastAPI endpoint to the public internet, which the frontend consumes.

### 1. Backend (Kaggle)
1. Generate the notebook locally: 
   ```bash
   python agent_backend/build_notebook.py
   ```
2. Push the notebook to Kaggle: 
   ```bash
   kaggle kernels push -p agent_backend/kaggle_submission/ --accelerator NvidiaTeslaT4
   ```
3. Wait for the Kaggle session to boot (can take 2-3 minutes). The API will automatically host itself on Localtunnel (`https://indic-finsight-seaadeep-998877.loca.lt`).

### 2. Frontend (Local)
Run the React application:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## API Testing

You can test the API directly using `cURL`. Make sure you pass the `Bypass-Tunnel-Reminder` header for Localtunnel.

```bash
curl -X POST https://indic-finsight-seaadeep-998877.loca.lt/chat \
  -H "Content-Type: application/json" \
  -H "Bypass-Tunnel-Reminder: true" \
  -d '{"text": "Show a chart of Reliance segment revenues", "history": []}'
```

Expected output includes the multi-agent reasoning trace (Thought, Action, Result) and a synthesized `Final Answer`.
