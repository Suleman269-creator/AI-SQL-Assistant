# 🤖 AI SQL Assistant

> An AI-powered SQL Assistant that converts natural language into SQL queries, executes them on a database, and provides intelligent business insights through an interactive dashboard.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite)
![Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4?logo=google)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Project Overview

AI SQL Assistant is a full-stack AI application that enables users to interact with databases using natural language instead of writing SQL manually.

Users can ask questions such as:

> *"Show the top 10 customers by revenue."*

The application uses Google's Gemini API to generate SQL queries, executes them against the database, and returns the results along with AI-generated business insights and visualizations.

---

## ✨ Features

- 💬 Natural Language to SQL Conversion
- 🤖 Google Gemini AI Integration
- 🗄️ SQLite Database Support
- ⚡ FastAPI REST Backend
- 🌐 React Frontend
- 📊 Interactive Data Visualization
- 📈 AI Business Insights
- 📝 Query History
- 📤 Export Results (CSV)
- 🔒 Clean & Scalable Project Architecture

---

## 🛠️ Tech Stack

### Frontend
- React.js
- Vite
- Axios
- Tailwind CSS

### Backend
- FastAPI
- Python
- SQLAlchemy
- Uvicorn

### AI
- Google Gemini API
- Prompt Engineering

### Database
- SQLite

### Tools
- Git
- GitHub
- VS Code
- Postman

---

## 📂 Project Structure

```text
AI-SQL-Assistant/
│
├── Frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── Backend/
│   ├── app/
│   │   ├── api/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── venv/
│
├── README.md
└── .gitignore
```

---

## 🏗️ System Architecture

```text
User
 │
 ▼
React Frontend
 │
 ▼
FastAPI REST API
 │
 ├─────────────► Google Gemini API
 │
 ▼
SQLite Database
 │
 ▼
Query Results
 │
 ▼
Business Insights & Dashboard
```

---

## 🚀 Getting Started

### Clone Repository

```bash
git clone https://github.com/yourusername/AI-SQL-Assistant.git
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

---

### Backend

```bash
cd Backend

python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

python -m uvicorn app.main:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

Swagger Docs:

```
http://127.0.0.1:8000/docs
```

Frontend:

```
http://localhost:5173
```

---

## 📅 Development Roadmap

- ✅ Project Setup
- ✅ React + FastAPI Architecture
- ✅ REST API Integration
- 🔄 React ↔ Backend Communication
- ⏳ Database Integration
- ⏳ Gemini AI Integration
- ⏳ SQL Generation
- ⏳ SQL Execution
- ⏳ Data Visualization
- ⏳ AI Business Insights
- ⏳ Authentication
- ⏳ Deployment

---

## 🎯 Learning Objectives

This project demonstrates practical experience in:

- Full-Stack Development
- AI Application Development
- REST API Design
- Prompt Engineering
- LLM Integration
- Backend Development
- Database Design
- React Development
- Software Architecture

---

## 📷 Screenshots

> Screenshots will be added as development progresses.

---

## 👨‍💻 Author

**Muhammad Suleman**

- LinkedIn: *https://www.linkedin.com/in/muhammad-suleman-1b88261b5/*
- GitHub: *https://github.com/Suleman269-creator*
- Email: **sulenagri@gmail.com**

---

## ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub.

It motivates me to continue building and sharing AI-powered open-source projects.