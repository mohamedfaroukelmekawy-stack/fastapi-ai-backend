#  FastAPI-LLM — AI Chat & File Analysis API

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![JWT](https://img.shields.io/badge/Auth-JWT-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A production-style **AI backend system** built with **FastAPI**, supporting:

* 🔐 JWT Authentication
* 💬 AI Chat API (LLM powered)
* 📄 PDF & Image Upload Analysis
* 🧠 Conversation Memory (Chat History)
* ⚡ Async database operations
* 🧩 Modular clean architecture

Designed as a **real-world backend architecture project** demonstrating modern Python backend engineering practices.

---

## 📌 Features

### ✅ Authentication

* User registration & login
* JWT token authentication
* Protected API routes
* Secure password hashing (bcrypt)

### ✅ AI Chat

* Conversational AI endpoint
* Context-aware chat history
* Persistent conversations per user

### ✅ File Analysis

Upload and analyze:

* 📄 PDF files
* 🖼 Images (OCR & content extraction)

Extracted content is automatically sent to the AI for analysis.

---

## 🏗 Architecture

```
app/
├── api/                # API routes
├── core/               # config & security
├── models/             # database models
├── schemas/            # Pydantic schemas
├── services/           # business logic
├── repositories/       # DB access layer
└── main.py             # FastAPI entrypoint
```

Architecture follows:

* Service Layer Pattern
* Repository Pattern
* Dependency Injection
* Clean separation of concerns

---

## ⚙️ Tech Stack

| Category        | Technology         |
| --------------- | ------------------ |
| Backend         | FastAPI            |
| Language        | Python 3.12        |
| Database        | PostgreSQL         |
| ORM             | SQLAlchemy (Async) |
| Auth            | JWT + OAuth2       |
| AI              | Cohere LLM API     |
| File Processing | Pillow, PyPDF      |
| Server          | Uvicorn            |

---

## 🔑 API Endpoints

### Authentication

```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Chat

```
POST   /api/chat
GET    /api/chat/history
DELETE /api/chat/history
```

### File Analysis

```
POST /api/chat/upload
```

---

## 🚀 Getting Started

### 1️⃣ Clone repository

```bash
git clone https://github.com/<your-username>/FastAPI-LLM.git
cd FastAPI-LLM
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Environment Variables

Create `.env`

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
COHERE_API_KEY=your_api_key
```

---

### 5️⃣ Run server

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

Swagger UI will appear.

---

## 🧪 Example Request

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{"message":"What is AI?"}'
```

---

## 🔒 Authentication Flow

```
Register → Login → Receive JWT → Use Token → Access Protected APIs
```

---

## 📷 Example Workflow

1. User logs in
2. Uploads PDF/image
3. Content extracted
4. Sent to LLM
5. AI returns analysis
6. Conversation stored in DB

---

## 🎯 Project Goals

This project demonstrates:

* Production-style FastAPI backend design
* Async Python development
* Secure authentication systems
* AI API integration
* Clean scalable architecture

---

## 📈 Future Improvements

* ✅ Docker deployment
* ✅ Streaming responses
* ✅ Role-based authorization
* ⏳ Frontend dashboard
* ⏳ Vector database (RAG)
* ⏳ Background task queue

---

## 👨‍💻 Author

**Mohamed Farouk**
Python Backend Developer | FastAPI | AI Integration

GitHub: https://github.com/mohamedfaroukelmekawy-stack

---

## ⭐ If you found this project useful

Give it a ⭐ on GitHub — it helps visibility!

---
