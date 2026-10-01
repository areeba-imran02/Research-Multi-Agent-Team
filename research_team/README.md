# Research Multi-Agent Team

Streamlit app: 4 AI agents (Planner, Researcher, Fact Checker, Writer) build a sourced report.
Model: Groq `openai/gpt-oss-20b` (free plan). Search: DuckDuckGo (no API key).

## Run locally
```
pip install -r requirements.txt
mkdir -p .streamlit
echo 'GROQ_API_KEY = "your_key_here"' > .streamlit/secrets.toml
streamlit run app.py
```

## Streamlit Cloud
1. Upload this folder to GitHub (main file: `app.py`).
2. App > Settings > Secrets:
   `GROQ_API_KEY = "your_key_here"`
3. Reboot the app.

## Optional secrets
- `GROQ_REASONING = "off"`  : turn off the low-reasoning option if Groq rejects it.
- `GROQ_MODEL = "groq/llama-3.1-8b-instant"` : try another free model.

## Free-plan notes
- Start with the **Quick** depth.
- When Groq's tokens-per-minute limit is hit, the app waits and continues by itself.
