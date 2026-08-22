# 🏥 Clinicon — Complete System Documentation & Deployment Guide

Welcome to **Clinicon**, an AI-powered smart clinic management and patient assistant platform. This document provides a complete overview of the system architecture, features, security implementations, and step-by-step setup instructions for deploying the entire system on a fresh machine from scratch.

---

## 📋 Table of Contents
1. [System Architecture Overview](#-system-architecture-overview)
2. [Simplified Non-Technical Guide (دليل غير الفنيين)](#-simplified-non-technical-guide-دليل-غير-الفنيين)
3. [Key Features & Recent Optimizations](#-key-features--recent-optimizations)
4. [Prerequisites & System Requirements](#-prerequisites--system-requirements)
5. [Step-by-Step Installation Guide (From Scratch)](#-step-by-step-installation-guide-from-scratch)
6. [Running the System](#-running-the-system)
7. [API Endpoints & Microservices Ports](#-api-endpoints--microservices-ports)
8. [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🏗️ System Architecture Overview

Clinicon consists of 4 main decoupled microservices operating seamlessly together:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                          React Frontend (Vite)                          │
│                          Port: 3000 (UI/UX)                             │
└─────────────────────────────────────────────────────────────────────────┘
        │                                             │
        │ /api (REST)                                 │ /agent/chat (JWT)
        ▼                                             ▼
┌───────────────────────────┐                 ┌───────────────────────────┐
│     FastAPI Backend       │                 │       Agent Server        │
│        Port: 5000         │                 │        Port: 8200        │
│  (Database, Auth, Slots,  │                 │ (LangChain + ReAct Loop)  │
│   Reminders, Doctor Leave)│                 └───────────────────────────┘
└───────────────────────────┘                               │
        ▲                                                   │ Tool Call (HTTP)
        │ DB Queries                                        ▼
┌───────────────────────────┐                 ┌───────────────────────────┐
│    SQLite / PostgreSQL    │                 │        RAG Server         │
│     (Patient Data DB)     │                 │        Port: 8100         │
└───────────────────────────┘                 │  (ChromaDB + BGE Embed)   │
                                              └───────────────────────────┘
```

---

## 🌟 Simplified Non-Technical Guide (دليل التشغيل المبسط لغير الفنيين)

إذا كنت شخصاً غير متخصص بالبرمجة أو التقنية وتريد تشغيل هذا النظام على جهازك بسهولة تامة، اتبع هذا الجزء:

### 1. كيف يتم الربط مع قاعدة البيانات PostgreSQL؟ (PostgreSQL Database Setup)

النظام مصمم للعمل مباشرة على قاعدة بيانات **PostgreSQL** عبر الرابط `DATABASE_URL`. يمكنك إعدادها بأحد الطريقين المقترحتين:

#### 🔹 الخيار الأول: التشغيل السريع باستخدام Docker (الأسهل)
إذا كان لديك **Docker Desktop** على الجهاز:
1. قم بتشغيل حاوية PostgreSQL بالأمر التالي:
   ```cmd
   docker run --name clinicon-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=clinic_db -p 5432:5432 -d postgres
   ```
2. هكذا أصبحت قاعدة بيانات PostgreSQL تعمل مباشرة على منفذ `5432`.

#### 🔹 الخيار الثاني: التثبيت المباشر لقاعدة PostgreSQL على الجهاز (Local Installation)
إذا كنت تثبت PostgreSQL كبرنامج عادي على الويندوز:
1. قم بتنزيل وتثبيت **PostgreSQL for Windows** من [موقع PostgreSQL الرسمي](https://www.postgresql.org/download/windows/).
2. أثناء التثبيت، حدد كلمة السر للـ `postgres` (مثلاً: `postgres`).
3. افتح برنامج **pgAdmin** أو موجه الأوامر واقطع أمر إنشاء قاعدة البيانات باسم `clinic_db`:
   ```sql
   CREATE DATABASE clinic_db;
   ```

#### 🔹 ضبط رابط قاعدة البيانات (File `.env`):
افتح مجلد `hospital/hospital/clinic-backend/` وقم بإنشاء أو تعديل ملف `.env` ووضع السطر التالي فيه:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clinic_db
SECRET_KEY=your-secret-key-here```
*(إذا كانت كلمة سر PostgreSQL مختلفة، استبدل `postgres:postgres` بـ `اسم_المستخدم:كلمة_السر` الخاصين بك).*

 عند تشغيل `setup-and-start.bat` أو الباك إند، ستقوم SQLAlchemy تلقائياً بإنشاء جميع الجداول الهيكلية داخل `clinic_db` فوراً!

---

### 2. خطوات التشغيل البسيطة (من البداية للنهاية):

1. **تثبيت المتطلبات الأساسية (مرة واحدة فقط عند أول استخدام):**
   - قم بتثبيت برنامج **Python 3.11** وقم بتعليم خيار *(Add Python to PATH)* أثناء التثبيت.
   - قم بتثبيت برنامج **Node.js**.
   - قم بتثبيت برنامج **Ollama** من موقع [ollama.com](https://ollama.com).
   - افتح موجه الأوامر (CMD) واكتب الأمر التالي لتنزيل نموذج الذكاء الاصطناعي:
     ```cmd
     ollama pull qwen3:4b
     ```

2. **تشغيل النظام بالكامل بنقرة واحدة:**
   - افتح مجلد المشروع `Clinicon`.
   - اضغط مرتين بالماوس (Double-click) على ملف **`setup-and-start.bat`**.
   - سينتظر الملف بضع ثوانٍ لتشغيل كافة سيرفرات النظام تلقائياً (الباك إند، سيرفر البحث، وسيرفر الذكاء الاصطناعي).

3. **دخول الموقع:**
   - افتح متصفح الإنترنت (Google Chrome / Edge) واذهب إلى العنوان:
     ```
     http://localhost:3000
     ```
   - مبروك! يمكنك الآن تجربة الموقع، تسجيل المرضى، واستخدام شات البوت الذكي مباشرة.

---

## ✨ Key Features & Recent Optimizations

### 1. 🔐 Security & Per-Patient Authentication
- **Token Isolation:** Eliminates static admin/bot tokens. Uses `contextvars` to pass the authenticated patient's JWT token per-request in a thread-safe manner.
- **Data Boundary:** Patients can only view/book their own appointments and access their own medical records.

### 2. 📅 Slot-Based Appointment Booking Architecture
- **Time Slots:** Replaced old walk-in queue numbers with fixed duration time-slots (e.g., 30 mins).
- **Available Slots API:** `GET /doctors/{doctor_id}/available-slots?date=YYYY-MM-DD` automatically calculates free slots taking into account doctor working hours, existing bookings, and doctor leave.

### 3. ⚡ Single-LLM High-Performance RAG Architecture
- **Fast Vector Retrieval:** `BAAI/bge-small-en-v1.5` running on CUDA FP16 yields search results from ChromaDB in **~0.1 seconds**.
- **Single-LLM Pipeline:** Eliminates dual-LLM overhead. Vector search returns raw context directly to the Agent (`qwen3:4b` via Ollama), reducing query response times from ~60s down to **10-15s**.
- **Multi-Threaded HTTP:** All python microservices run on `ThreadingHTTPServer` to prevent IO blocking and request timeouts.

---

## 💻 Prerequisites & System Requirements

### Hardware Requirements:
- **GPU:** NVIDIA GPU with at least **4GB VRAM** (e.g., NVIDIA T500, GTX 1650, RTX 3050 or higher).
- **RAM:** Minimum 16GB System RAM.
- **Storage:** 15GB free SSD space.

### Software Requirements:
- **OS:** Windows 10/11 or Ubuntu Linux 20.04+.
- **Python:** Python 3.11 (Recommended).
- **Node.js:** Node.js v18+ & npm.
- **CUDA:** NVIDIA CUDA Toolkit 11.8 or 12.x + cuDNN.
- **Ollama:** Ollama for Windows/Linux ([Download Ollama](https://ollama.com/download)).

---

## 🛠️ Step-by-Step Installation Guide (From Scratch)

Follow these exact steps to set up a brand new machine from zero.

### Step 1: Clone the Repository
```bash
git clone https://github.com/yassenahmedbakry-oss/Clinicon.git
cd Clinicon
```

### Step 2: Install Ollama & Pull the Model
1. Download and install **Ollama** from [https://ollama.com](https://ollama.com).
2. Open terminal/command prompt and pull the Qwen 3 4B model:
```bash
ollama pull qwen3:4b
```
*(Verify it works by running `ollama run qwen3:4b "hello"`, then exit with `/bye`)*.

### Step 3: Install Python Dependencies & PyTorch with CUDA
Create a virtual environment (optional but recommended) and install dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate
# Activate on Linux/macOS: source venv/bin/activate

# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install project requirements
pip install -r requirements.txt
```

### Step 4: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 5: Build ChromaDB Vector Store
Initialize and build the medical knowledge vector store with BGE Embeddings:
```bash
python rebuild_chroma.py
```
*(This will download `BAAI/bge-small-en-v1.5` embeddings model and populate `rag/database/chroma_db`)*.

---

## 🚀 Running the System

You can launch all 4 microservices simultaneously using the automated script:

### Windows:
Simply run:
```cmd
.\setup-and-start.bat
```

### Manual Execution (Individual Terminals):
If you prefer running services separately for debugging:

1. **Terminal 1: FastAPI Backend (Port 5000)**
   ```bash
   cd hospital/hospital/clinic-backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
   ```

2. **Terminal 2: RAG Server (Port 8100)**
   ```bash
   python rag_server.py
   ```

3. **Terminal 3: Agent Server (Port 8200)**
   ```bash
   python agent_server.py
   ```

4. **Terminal 4: React Frontend (Port 3000)**
   ```bash
   cd frontend
   npm run dev
   ```

---

## 🌐 API Endpoints & Microservices Ports

| Service | Host | Port | Main Responsibility |
|---|---|---|---|
| **Frontend** | `http://localhost:3000` | 3000 | React Web UI / Patient & Doctor Portals |
| **Backend API** | `http://127.0.0.1:5000` | 5000 | Database, Users, Slot Bookings, Doctor Leave |
| **RAG Server** | `http://127.0.0.1:8100` | 8100 | BGE Vector Search (`POST /search`) |
| **Agent Server**| `http://127.0.0.1:8200` | 8200 | LangChain AI Chatbot Agent (`POST /chat`) |

---

## ❓ Troubleshooting & FAQs

### Q1: `ConnectionAbortedError [WinError 10053]` in Agent Server
- **Cause:** Frontend request timed out or client closed browser tab while AI was thinking.
- **Fix:** System automatically catches socket exceptions safely without crashing the thread. Ensure frontend timeout is set to 300s.

### Q2: `ECONNREFUSED` on Vite Frontend Proxy
- **Cause:** Vite was proxying `localhost` to IPv6 (`::1`) while Python bound to IPv4 (`127.0.0.1`).
- **Fix:** In `frontend/vite.config.js`, proxy targets are set explicitly to `http://127.0.0.1:8200` and `http://127.0.0.1:5000`.

### Q3: How to verify GPU Acceleration?
Run the following Python check:
```python
import torch
print("CUDA Available:", torch.cuda.is_available())
print("Device:", torch.cuda.get_device_name(0))
```
It should output `CUDA Available: True` with your GPU model.
