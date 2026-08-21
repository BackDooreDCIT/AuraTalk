# AuraTalk - Complete Setup Guide

This document records the complete environment setup that was performed for this project. Use this guide if you ever need to set up the project on a new machine.

## Prerequisites Installed

1. **Python 3.12**
   - The project requires Python 3.12. (Python 3.14 was too new for PyTorch).
   - Installed via winget: `winget install Python.Python.3.12`

2. **FFmpeg 9.0**
   - Required for audio conversion (e.g., converting `.webm` to `.wav` for speech transcription).
   - Installed via winget: `winget install Gyan.FFmpeg`

## Environment Setup

1. **Virtual Environment**
   - A virtual environment named `.venv` was created in the project root.
   - Command used: `py -3.12 -m venv .venv`
   - **Note:** Added `.venv` to `.gitignore` so it doesn't get tracked by git.

2. **Environment Variables**
   - The file `env` was renamed to `.env` so `python-dotenv` can properly load it.
   - It contains the necessary keys: `DATABASE_URL`, `API_DATABASE`, `API_VAJA`, and `POSTGRES_URL`.

## Python Dependencies

The following packages were installed into the `.venv` environment:

1. **PyTorch with CUDA** (for GPU-accelerated AI)
   - Installed specifically with CUDA 12.1 support to utilize the NVIDIA RTX 4060 GPU.
   - Command used: `.venv\Scripts\pip.exe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

2. **Remaining Requirements**
   - Replaced `psycopg2` with `psycopg2-binary` to avoid build errors on Windows.
   - Installed all other dependencies defined in `requirements.txt`.
   - Command used: `.venv\Scripts\pip.exe install uvicorn "fastapi[standard]" python-dotenv supabase sqlalchemy ffmpeg-python librosa transformers "bcrypt==3.2.2" passlib psycopg2-binary`

## How to Run the Application

Now that everything is installed, you can start the application using the following command:

```powershell
# Activate the virtual environment
.venv\Scripts\activate

# Run the FastAPI server
uvicorn main:app --reload
```

The application will be accessible at: **http://127.0.0.1:8000**
