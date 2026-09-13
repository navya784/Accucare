#ACCUCARE 
# AccuCare

**AccuCare** is a Clinical Decision Support System (CDSS) built to assist doctors by combining a retrieval-augmented AI pipeline with structured patient record management. It grounds its responses in trusted clinical guideline documents, helping ensure that AI-assisted suggestions are traceable back to verified medical sources rather than relying on unchecked model outputs.

---

## 🩺 Overview

AccuCare lets clinicians:
- Chat with an AI assistant that answers clinical questions **grounded in real guideline documents** (not just model memory)
- View **cited sources** for every AI-generated response, so answers can be verified against the original guideline text
- Maintain structured **patient records** and **chat history** across sessions
- Generate **downloadable PDF reports** summarizing patient consultations

The goal is to reduce the risk of hallucinated or unverifiable medical suggestions by combining Retrieval-Augmented Generation (RAG) with strict citation verification.

---
<img width="1436" height="756" alt="Screenshot 2026-09-13 222647" src="https://github.com/user-attachments/assets/01185280-e0ef-4fd0-9eda-36ae3562aa7e" />
<img width="1440" height="764" alt="Screenshot 2026-09-13 222502" src="https://github.com/user-attachments/assets/aa0d08d6-6a29-4387-8e12-b7e39055ab27" />

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend | Streamlit |
| RAG Pipeline | LangChain |
| Vector Store | ChromaDB |
| Database | SQLite (via SQLAlchemy ORM) |
| PDF Generation | ReportLab |

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌───────────────────┐
│  Streamlit   │ <--> │   FastAPI     │ <--> │   SQLite (via      │
│  Frontend    │      │   Backend     │      │   SQLAlchemy)      │
└─────────────┘      └──────┬───────┘      │ Patient / Report /  │
                              │              │ ChatHistory models  │
                              ▼              └───────────────────┘
                     ┌─────────────────┐
                     │  LangChain RAG   │
                     │  Pipeline         │
                     └────────┬────────┘
                              ▼
                     ┌─────────────────┐
                     │   ChromaDB        │
                     │ (Vector Store —   │
                     │  guideline docs)  │
                     └─────────────────┘
```

1. A doctor asks a clinical question via the Streamlit chat interface.
2. FastAPI routes the query to the LangChain RAG pipeline.
3. The pipeline retrieves relevant chunks from trusted clinical guideline documents (embedded and stored in ChromaDB).
4. The retrieved context + query are passed to the LLM to generate a grounded response.
5. Responses are cross-checked against source documents (citation verification) before being returned.
6. Patient details, chat history, and generated reports are persisted via SQLAlchemy/SQLite.
7. Reports can be exported as PDF via ReportLab.

---

## ✨ Features

- 🔍 **Retrieval-Augmented Generation** — answers are grounded in actual clinical guideline documents, not just the LLM's internal knowledge
- ✅ **Citation verification** — traces AI responses back to their source documents for transparency and trust
- 🗂️ **Patient record management** — structured storage of patient details, session history, and generated reports
- 💬 **Persistent chat history** — conversations are saved and retrievable across sessions
- 📄 **PDF report generation** — export patient consultation summaries as professional PDF reports
- 🖥️ **Simple, clean UI** — built with Streamlit for quick clinician-facing interaction

---

## 📁 Project Structure

```
accucare/
├── backend/
│   ├── app.py                  # FastAPI app entrypoint
│   ├── models.py               # SQLAlchemy models (Patient, Report, ChatHistory)
│   ├── database.py             # DB connection/session setup
│   ├── rag/
│   │   ├── ingest.py            # Script to embed guideline PDFs into ChromaDB
│   │   ├── retriever.py         # LangChain retriever setup
│   │   └── chain.py             # RAG chain + citation verification logic
│   ├── reports/
│   │   └── generate_report.py   # ReportLab PDF generation
│   ├── chroma_db/               # (generated locally — not tracked in git)
│   └── data/
│       └── guidelines/          # Source clinical guideline PDFs
├── frontend/
│   └── app.py                  # Streamlit frontend
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip / virtualenv

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/accucare.git
cd accucare
```

### 2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in required values (e.g., API keys):
```bash
cp .env.example .env
```

### 5. Build the vector store
ChromaDB data is **not included in this repo** (it's generated locally). Run the ingestion script to embed the guideline documents:
```bash
python backend/rag/ingest.py
```

### 6. Run the backend
```bash
uvicorn app:app --reload --port 8000
```

### 7. Run the frontend
In a separate terminal:
```bash
streamlit run streamlit_app.py
```

---

## 🗺️ Roadmap

- [x] FastAPI + Streamlit base setup
- [x] RAG pipeline with LangChain + ChromaDB
- [x] Patient / Report / ChatHistory persistence
- [x] PDF report generation
- [ ] Citation verification refinement
- [ ] Multi-user authentication
- [ ] Deployment (Docker + cloud hosting)

---

## ⚠️ Disclaimer

AccuCare is a research/academic project intended to demonstrate AI-assisted clinical decision support. It is **not a certified medical device** and should not be used for real clinical decision-making without appropriate validation, regulatory approval, and human oversight.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
