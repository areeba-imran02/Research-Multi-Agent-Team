# Research Multi-Agent Team

A professional multi-agent research application built with **CrewAI, Groq, and Streamlit**.

The system uses a team of specialised AI agents to plan research, search the web, verify information, and generate a structured research report.

---

## Overview

**Research Multi-Agent Team** transforms a research topic into a structured report through a sequential multi-agent workflow.

Instead of relying on a single AI response, the application divides the research process between specialised agents.

### Workflow

```text
User
  │
  ▼
Streamlit Interface
  │
  ▼
Research Planner
  │
  ▼
Web Researcher
  │
  ▼
Fact Checker
  │
  ▼
Report Writer
  │
  ▼
Final Research Report
```

---

## Features

* Multi-agent research workflow
* Research planning
* Real web-based research
* Fact and source verification
* Structured report generation
* Source attribution
* Multiple research-depth options
* Professional Streamlit interface
* Downloadable research report
* Secure API-key handling through environment variables/Streamlit Secrets
* Modular project architecture

---

## AI Agents

### 1. Research Planner

Breaks the user's research topic into focused research questions and creates a structured research plan.

### 2. Web Researcher

Uses the web-search tool to find relevant information, facts, statistics, and sources related to the research plan.

### 3. Fact Checker

Reviews the collected research and verifies important claims using available web sources.

### 4. Report Writer

Uses the verified research to create a clear and structured final research report with sources.

---

## Technology Stack

| Technology                | Purpose                       |
| ------------------------- | ----------------------------- |
| Python                    | Core programming language     |
| Streamlit                 | Web interface                 |
| CrewAI                    | Multi-agent orchestration     |
| Groq                      | Large Language Model provider |
| GPT-OSS 20B               | Primary language model        |
| Web Search Tool           | External research             |
| GitHub                    | Source code repository        |
| Streamlit Community Cloud | Deployment                    |

---

## Project Structure

```text
research-multi-agent/
│
├── app.py
├── requirements.txt
├── README.md
│
├── config/
│   └── groq_config.py
│
├── agents/
│   ├── planner.py
│   ├── researcher.py
│   ├── fact_checker.py
│   └── report_writer.py
│
├── tasks/
│   ├── planning.py
│   ├── research.py
│   ├── fact_check.py
│   └── report.py
│
├── tools/
│   └── web_search.py
│
└── crew/
    └── research_crew.py
```

---

## How It Works

### Step 1 — Enter a Research Topic

The user enters a topic into the Streamlit interface.

Example:

```text
Impact of Artificial Intelligence on Education
```

### Step 2 — Research Planning

The Research Planner identifies the important areas that need to be investigated.

### Step 3 — Web Research

The Web Researcher uses an external web-search tool to collect relevant information and sources.

### Step 4 — Fact Checking

The Fact Checker examines important claims and verifies them against available sources.

### Step 5 — Report Generation

The Report Writer transforms the verified research into a structured report.

---

## Environment Variables

The application requires API credentials for the AI model and web-search service.

Required secrets may include:

```text
GROQ_API_KEY
SERPER_API_KEY
```

**Never place API keys directly inside Python files or commit them to GitHub.**

For Streamlit Community Cloud, add the required credentials through the application's **Secrets** settings.

---

## Groq Configuration

The project uses Groq's OpenAI-compatible API endpoint:

```text
https://api.groq.com/openai/v1
```

The primary model is:

```text
openai/gpt-oss-20b
```

The API key is loaded securely through the environment/Streamlit Secrets.

---

## Running on Streamlit Community Cloud

The project is designed to be deployed directly from GitHub.

### Deployment flow

```text
GitHub Repository
       ↓
Streamlit Community Cloud
       ↓
Select Repository
       ↓
Select app.py
       ↓
Add Secrets
       ↓
Deploy
```

The application dependencies are defined in:

```text
requirements.txt
```

---

## Security

API keys should never be committed to the repository.

Do not add:

```text
.env
```

or hard-coded API keys to GitHub.

Use Streamlit Secrets or environment variables instead.

---

## Research Quality

The application is designed to separate:

```text
Planning
   ↓
Research
   ↓
Verification
   ↓
Writing
```

The fact-checking stage provides an additional verification layer before the final report is generated.

However, AI-generated research can still contain errors. Important information should be independently reviewed before being used for academic, professional, legal, medical, financial, or other high-stakes purposes.

---

## Future Improvements

Possible future enhancements include:

* Multiple specialised research domains
* Parallel research agents
* PDF report generation
* DOCX report generation
* Citation formatting
* Source-quality scoring
* Research history
* Advanced source comparison
* Research export options
* Additional search providers

These features are intentionally outside the scope of the first version.

---

## Project Goal

The goal of this project is to demonstrate how multiple specialised AI agents can collaborate through **CrewAI** to perform a structured research workflow.

```text
Plan → Research → Verify → Report
```

---

## Author

**Areeba Imran**

BS Information Technology Student
University of Agriculture Faisalabad

---

## License

This project is intended for educational and portfolio purposes.
