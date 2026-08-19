# TheraTalk — Project Overview & Setup Guide

## What is TheraTalk?
A **Python/FastAPI web application** designed to help **Aphasia patients** practice speaking exercises. It has two user roles:
- **SLP (Speech-Language Pathologist)** — manages patients, assigns lessons, checks progress
- **Patient** — completes speaking exercises with AI-powered speech recognition

> [!NOTE]
> Semifinalist at NSC 2025 and Honorable Award winner at AI Thailand Hackathon 2024.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | **FastAPI** (Python) with **Uvicorn** server |
| Frontend | **Jinja2 templates** + vanilla HTML/CSS/JS |
| Database | **Supabase** (hosted PostgreSQL via API) |
| AI/ML | **Whisper** (Thai speech-to-text via `transformers`) + **PyTorch** |
| TTS | **VAJA API** (AI for Thai text-to-speech) |
| Audio | **FFmpeg** (audio format conversion) |
| Auth | **bcrypt** via `passlib` (password hashing) |

---

## Project Structure

```
theratalk/
├── main.py                    # FastAPI app entry point (login, signup, TTS API, logout)
├── requirements.txt           # Python dependencies
├── installation.md            # Original setup notes (Thai/English)
├── readme.md                  # Project info & license
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── db/
│   │   ├── db.py              # Supabase client setup + helper functions
│   │   ├── crud.py            # CRUD operations (minimal)
│   │   ├── models.py          # SQLAlchemy models (mostly unused)
│   │   └── schemas.py         # Pydantic schemas (minimal)
│   └── routers/
│       ├── userRoute.py       # Patient routes: home, lessons, speech transcription, answer checking
│       └── docRoute.py        # SLP routes: home, patient management, assignments, progress checking
├── templates/                 # 31 Jinja2 HTML templates
│   ├── disclaimer.html        # Landing page
│   ├── testlogin.html         # Login page
│   ├── signup.html            # SLP signup
│   ├── home_patient.html      # Patient dashboard
│   ├── home_p.html            # SLP dashboard
│   ├── les_*.html             # Various lesson types (listen & speak, sequencing, short story, etc.)
│   └── ...more
├── static/
│   ├── css/                   # 23 CSS files (per-page styling)
│   ├── js/                    # 6 JS files (assignment, audio playback, voice recording)
│   ├── img/                   # Images and activity assets
│   └── sounds/                # Sound effects (correct.mp3)
└── fak/                       # Test data
    ├── dataset/               # JSON test datasets
    └── sql/                   # SQL schema files
```

---

## Your Current Environment

| Component | Status |
|-----------|--------|
| Python | ✅ **3.14.4** installed |
| pip | ✅ **26.0.1** installed |
| Node.js | ✅ **v24.18.0** installed (not strictly needed for this project) |
| GPU | ✅ **NVIDIA RTX 4060 Laptop** (8GB VRAM, CUDA 13.2) |
| FFmpeg | ❌ **NOT installed** |
| `.env` file | ❌ **NOT found** (required for API keys) |
| Python packages | ❌ **Almost none installed** (only `requests`, `certifi`, etc.) |

---

## What You Need to Install

### Step 1 — Install FFmpeg (required for audio processing)

FFmpeg is needed by the speech transcription feature to convert `.webm` audio to `.wav`. Install via Chocolatey:

```powershell
choco install ffmpeg -y
```

> [!IMPORTANT]
> If you don't have Chocolatey, install it first — see [installation.md](file:///c:/Users/Acer/Desktop/theratalk/installation.md) for the PowerShell command, or download FFmpeg manually from https://ffmpeg.org/download.html.

### Step 2 — Install PyTorch with CUDA (for GPU-accelerated AI)

Since you have an RTX 4060, install the CUDA-enabled PyTorch **before** the rest of requirements.txt:

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

> [!NOTE]
> Your GPU supports CUDA 13.2, so `cu121` wheels will work fine. This replaces the generic `torch` from requirements.txt.

### Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

> [!WARNING]
> **`psycopg2`** may fail to build on Windows. If it does, use `psycopg2-binary` instead:
> ```powershell
> pip install psycopg2-binary
> ```
> Then install the rest normally.

### Step 4 — Create the `.env` file

The app requires a `.env` file in the project root with these keys:

```env
DATABASE_URL=<your-supabase-project-url>
API_DATABASE=<your-supabase-anon-or-service-key>
API_VAJA=<your-vaja-tts-api-key>
```

| Variable | Source |
|----------|--------|
| `DATABASE_URL` | Supabase project URL (e.g. `https://xxxx.supabase.co`) |
| `API_DATABASE` | Supabase API key (anon or service role) |
| `API_VAJA` | VAJA TTS API key from [aiforthai.in.th](https://aiforthai.in.th) |

> [!CAUTION]
> **Without the `.env` file, the app will crash immediately** on startup because [db.py](file:///c:/Users/Acer/Desktop/theratalk/app/db/db.py) calls `create_client()` with `None` values.

### Step 5 — Run the app

```powershell
uvicorn main:app --reload
```

The app will be available at **http://127.0.0.1:8000**

---

## Quick Install Summary (copy-paste order)

```powershell
# 1. Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Install remaining Python packages
pip install -r requirements.txt

# 3. If psycopg2 fails, use binary version
pip install psycopg2-binary

# 4. Install FFmpeg (requires Chocolatey or manual install)
choco install ffmpeg -y

# 5. Create .env file (fill in your keys!)
# 6. Run the server
uvicorn main:app --reload
```
