import nbformat as nbf
import json

nb = nbf.v4.new_notebook()

# Intro Markdown
intro_md = """# Indic-FinSight: Multi-Agent Financial Analyst
**Kaggle Submission — Gemma 4 Hybrid**
"""

# Installs
installs = """!pip install -q -U chromadb fastembed yfinance transformers accelerate bitsandbytes fastapi uvicorn pydantic nest-asyncio duckduckgo-search wikipedia numexpr
!npm install -g localtunnel"""

with open("extracted_notebook.py", "r") as f:
    code = f.read()

# Filter out the # CELL markers
lines = code.split("\n")
clean_lines = [l for l in lines if not l.startswith("# CELL")]
clean_code = "\n".join(clean_lines)

nb['cells'] = [
    nbf.v4.new_markdown_cell(intro_md),
    nbf.v4.new_code_cell(installs),
    nbf.v4.new_code_cell(clean_code)
]

nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.10"
    }
}

with open('agent_backend/kaggle_submission/notebook.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Notebook generated successfully.")
