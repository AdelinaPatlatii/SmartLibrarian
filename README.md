# SmartLibrarian

SmartLibrarian is a production-style FastAPI + React (Vite) app that recommends books using Retrieval-Augmented Generation (RAG). It can also:

🎙️ Transcribe your voice prompt (STT, mic recording in the browser)

🔊 Read the assistant’s answer aloud (TTS)

🎨 Generate an image inspired by the recommended book

🛡️ Moderate the input for offensive/inappropriate prompts

All generated media (audio & images) is saved under a static/ folder and served by FastAPI.

# Features

- RAG recommendations (ChromaDB + LLM)
- Content moderation for user prompts
- Speech-to-Text (STT) via mic recording (OpenAI Whisper)
- Text-to-Speech (TTS) for the answer (OpenAI TTS)
- Image generation based on the chosen title

# Tech Stack

- Backend: FastAPI, Uvicorn, Python 3.9+
- RAG: ChromaDB
- LLM / Media: OpenAI API (whisper-1, gpt-image-1, gpt-4o-mini-tts)
- Frontend: React + TypeScript + Vite

# Project Structure
```
.
├── server.py                     # FastAPI app + endpoints + static serving
├── app.py                        # CLI runner: interactive loop using STT/moderation/RAG/LLM; optional TTS & image generation
├── db.py                         # ChromaDB setup
├── rag.py                        # retrieve candidate books from the database
├── llm.py                        # uses OpenAI API to construct the recommendation
├── llm_tools.py                  # local function tools for LLM: book summaries dict + get_summary_by_title tool definition
├── moderation.py                 # for moderating the user prompts
├── image_generation.py           # handles image generation
├── audio_io.py                   # handles speech to text and text to speech transcription
├── static/                       # served at "/" (generated .png/.mp3 land here)
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx              # UI: Ask, Record input prompt, Read aloud, Generate image
│       └── App.css              # UI styles
└── .env                         # OPENAI_API_KEY and VITE_API_BASE_URL are stored here
```

FastAPI mounts static/ at /, so URLs like /micul_print.png or /micul_print.mp3 are directly accessible.

---

## Installing and running the application

1. **Clone the repository and navigate to the directory** `TheFancyCalculator`:
    ```bash
   git clone https://github.com/AdelinaPatlatii/SmartLibrarian.git
   cd SmartLibrarian
   
2. **Create your `.env` file based on the provided template:**
   ```bash
   OPENAI_API_KEY=<your-openai-api-key-goes-here>
   VITE_API_BASE_URL=http://localhost:2050

3. **Install the required dependencies and run FastAPI:**
   ```bash
   pip install -r requirements.txt
   uvicorn server:app --host 0.0.0.0 --port 2050 --reload

The API will be at: http://localhost:2050

4. **Run the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev

The UI will be at: http://localhost:5173

5. **Visit the app in your browser:**

   http://localhost:5173
