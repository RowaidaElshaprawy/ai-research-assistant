# ai-research-assistant
# 🔬 Autonomous AI Research Assistant

An intelligent multi-agent system that automatically searches academic papers, analyzes findings, and generates comprehensive literature reviews — powered by LangGraph, Groq LLaMA, and arXiv.

---

## 🧠 How It Works

When you type a research topic, five AI agents work as a team in sequence:

```
User Query
    ↓
🗂️  Coordinator   → Plans the research strategy
    ↓
🔍  Searcher      → Fetches real papers from arXiv
    ↓
📊  Analyzer      → Extracts key findings from each paper
    ↓
✍️  Synthesizer   → Writes a cohesive literature review
    ↓
📎  Citation Manager → Polishes the report and adds citations
    ↓
Downloadable Report (Markdown / TXT)
```

---

## 🗂️ Project Structure

```
ai-research-assistant/
│
├── backend/
│   ├── .env                  ← Your secret API key (never pushed to GitHub)
│   ├── requirements.txt      ← Python dependencies for the backend
│   ├── agents.py             ← The 5 AI agents + LangGraph pipeline
│   └── main.py               ← FastAPI server + SQLite history
│
├── frontend/
│   ├── requirements.txt      ← Streamlit + requests
│   └── app.py                ← The Streamlit web interface
│
├── .gitignore                ← Keeps .env and venv out of GitHub
└── README.md                 ← You are here
```

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Web UI — pure Python, no HTML needed |
| Backend | FastAPI + Uvicorn | REST API server |
| Agents | LangGraph + LangChain | Multi-agent pipeline orchestration |
| LLM | Groq (LLaMA 3.3 70B) | Powers all 5 agents — fast and free |
| Search | arXiv API | Fetches real academic papers |
| Vector DB | ChromaDB | Indexes and retrieves paper content |
| Database | SQLite + SQLAlchemy | Stores research history locally |
| Secrets | python-dotenv | Loads API keys from .env safely |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A free [Groq API key](https://console.groq.com)
- VS Code (recommended)

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-research-assistant.git
cd ai-research-assistant
```

---

### 2. Set Up the Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create your `.env` file inside the `backend/` folder:

```
GROQ_KEY=your_actual_groq_api_key_here
```

> ⚠️ Never share or push this file. It is listed in `.gitignore` for your protection.

---

### 3. Set Up the Frontend

Open a **new terminal**, then:

```bash
cd frontend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

---

### 4. Run the Project

You need **two terminals open at the same time**.

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate
python main.py
```
You should see: `Uvicorn running on http://0.0.0.0:8002`

**Terminal 2 — Frontend:**
```bash
cd frontend
venv\Scripts\activate
streamlit run app.py
```
Your browser opens at: `http://localhost:8501`

---

## 🖥️ Using the App

1. Type a research topic in the input box (e.g. `Transformer Architectures in NLP`)
2. Click **Start Research**
3. Wait 1–2 minutes while the agents work
4. Read your generated literature review
5. Download it as Markdown or plain text
6. View past research in the **sidebar history**

---

## 🔒 Security Notes

- Your `.env` file is listed in `.gitignore` — it will **never** be pushed to GitHub
- Your virtual environments (`venv/`) are also excluded
- Never paste your API key directly into any `.py` file

---

## 🌱 Future Improvements

- [ ] PDF export with proper formatting
- [ ] Support for more paper databases (Semantic Scholar, PubMed)
- [ ] User-selectable number of papers to fetch
- [ ] Side-by-side paper comparison view
- [ ] Deploy to cloud (Railway, Render, or Hugging Face Spaces)

---

## 👩‍💻 Author

**Rowaida Elshaprawy**  
Built from scratch as a learning project in Python, FastAPI, and multi-agent AI systems.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
