import React, { useMemo, useState } from "react";

/**
 * SmartLibrarian React App
 *
 * This component is a minimal UI that talks to your Python backend.
 * It supports:
 *  - Sending a question to /api/chat → shows LLM answer (+ optional chosen_title/summary)
 *  - Generating an image via /api/image
 *  - Generating audio via /api/tts
 *  - Speech-to-Text via /api/stt (audio file upload)
 *
 * The base URL is configured via Vite env:
 *  VITE_API_BASE_URL=https://your-api-host
 *  (defaults to http://localhost:8000 for local dev)
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:2050";

/** Shapes of the backend responses (TypeScript typing) */
type ChatResponse = {
  answer: string;
  chosen_title?: string;
  summary?: string;
};

type ImageResponse = { image_url: string };
type TTSResponse = { audio_url: string };
type STTResponse = { text: string };

/** Small helper: POST JSON to a backend endpoint and parse the result */
async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

/** Small helper: POST multipart/form-data (for audio files) */
async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

/**
 * App component:
 * Holds all local UI state and wires up handlers to call the backend.
 */
export default function App() {
  // ------- Core chat state -------
  const [userQ, setUserQ] = useState("");                     // user input text
  const [answer, setAnswer] = useState("");                   // assistant's answer text
  const [chosenTitle, setChosenTitle] = useState<string>();   // which book was selected
  const [summary, setSummary] = useState<string>();           // summary text for chosen book

  // ------- Media URLs (returned by backend) -------
  const [imageUrl, setImageUrl] = useState<string>();         // generated image URL
  const [audioUrl, setAudioUrl] = useState<string>();         // generated audio URL

  // ------- Loading flags + error -------
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadingImage, setLoadingImage] = useState(false);
  const [loadingTTS, setLoadingTTS] = useState(false);
  const [loadingSTT, setLoadingSTT] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derived flags to enable/disable action buttons
  const canGenImage = useMemo(() => !!chosenTitle && !!summary, [chosenTitle, summary]);
  const canTTS = useMemo(() => answer.trim().length > 0, [answer]);

  /**
   * Handler: send the user's question to /api/chat.
   * Resets media state and populates answer/title/summary from backend.
   */
  async function onSend() {
    if (!userQ.trim()) return;
    setError(null);
    setLoadingChat(true);
    setAnswer("");
    setChosenTitle(undefined);
    setSummary(undefined);
    setImageUrl(undefined);
    setAudioUrl(undefined);

    try {
      const res = await postJSON<ChatResponse>("/api/chat", { user_q: userQ });
      setAnswer(res.answer);
      setChosenTitle(res.chosen_title);
      setSummary(res.summary);
    } catch (e: any) {
      setError(e.message || "Request failed");
    } finally {
      setLoadingChat(false);
    }
  }

  /**
   * Handler: ask backend to generate an image for the chosen title.
   * Requires both chosenTitle and summary (to build a rich prompt server-side).
   */
  async function onGenerateImage() {
    if (!canGenImage || !chosenTitle || !summary) return;
    setLoadingImage(true);
    setError(null);
    setImageUrl(undefined);
    try {
      const res = await postJSON<ImageResponse>("/api/image", {
        title: chosenTitle,
        summary,
      });
      setImageUrl(res.image_url);
    } catch (e: any) {
      setError(e.message || "Image generation failed");
    } finally {
      setLoadingImage(false);
    }
  }

  /**
   * Handler: ask backend to synthesize TTS audio of the assistant's answer text.
   */
  async function onTTS() {
    if (!canTTS) return;
    setLoadingTTS(true);
    setError(null);
    setAudioUrl(undefined);
    try {
      const res = await postJSON<TTSResponse>("/api/tts", { text: answer });
      setAudioUrl(res.audio_url);
    } catch (e: any) {
      setError(e.message || "TTS failed");
    } finally {
      setLoadingTTS(false);
    }
  }

  /**
   * Handler: upload an audio file for STT transcription.
   * On success, it populates the query box with the transcribed text.
   */
  async function onSTTFile(file: File, language?: string) {
    setLoadingSTT(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      if (language) form.append("language", language);
      const res = await postForm<STTResponse>("/api/stt", form);
      setUserQ(res.text || "");
    } catch (e: any) {
      setError(e.message || "STT failed");
    } finally {
      setLoadingSTT(false);
    }
  }

  // ----------------- Render -----------------
  return (
    <div className="min-h-screen">
      <header className="container header">
        <h1 className="h1">📚 SmartLibrarian</h1>
        <p className="subtle">
          RAG + LLM book recommendations • optional image generation • speech I/O
        </p>
      </header>

      <main className="container" style={{ paddingBottom: "6rem" }}>
        {/* Query box */}
        <section className="panel">
          <label className="block text-sm font-medium mb-2">Your question</label>
          <textarea
            className="textarea"
            rows={3}
            placeholder='Ex: „Vreau o carte despre prietenie și magie”'
            value={userQ}
            onChange={(e) => setUserQ(e.target.value)}
          />
          <div className="row">
            <button
              onClick={onSend}
              disabled={loadingChat}
              className="btn btn-blue"
            >
              {loadingChat ? "Thinking…" : "Ask"}
            </button>

            {/* STT upload */}
            <label className="ml-auto subtle">STT (upload audio):</label>
            <input
              type="file"
              accept="audio/*"
              disabled={loadingSTT}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onSTTFile(f, "ro");
              }}
              className="text-sm"
            />
            {loadingSTT && <span className="subtle">Transcribing…</span>}
          </div>
        </section>

        {/* Errors */}
        {error && (
          <div className="mt-4 error">
            {error}
          </div>
        )}

        {/* Answer card */}
        {answer && (
          <section className="mt-6 panel">
            <div className="card-title">Assistant</div>
            <div className="answer">{answer}</div>

            {/* Actions */}
            <div className="mt-4 row" style={{ flexWrap: "wrap" }}>
              <button
                onClick={onTTS}
                disabled={!canTTS || loadingTTS}
                className="btn btn-purple"
              >
                {loadingTTS ? "Generating audio…" : "🔊 Read aloud"}
              </button>

              <button
                onClick={onGenerateImage}
                disabled={!canGenImage || loadingImage}
                className="btn btn-green"
              >
                {loadingImage ? "Generating image…" : "🎨 Generate image"}
              </button>
            </div>

            {/* Media links */}
            <div className="mt-3" style={{ display: "grid", gap: ".5rem" }}>
              {audioUrl && (
                <div className="media-box">
                  <div className="text-sm" style={{ fontWeight: 600, marginBottom: ".25rem" }}>
                    Audio
                  </div>
                  <audio controls src={audioUrl} style={{ width: "100%" }} />
                </div>
              )}
              {imageUrl && (
                <div className="media-box">
                  <div className="text-sm" style={{ fontWeight: 600, marginBottom: ".5rem" }}>
                    Generated image
                  </div>
                  <a href={imageUrl} target="_blank" rel="noreferrer">
                    <img
                      src={imageUrl}
                      className="rounded-xl"
                      style={{ border: `1px solid var(--border)`, maxHeight: 512, objectFit: "contain", width: "100%" }}
                      alt="Generated"
                    />
                  </a>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      <footer className="footer">
        SmartLibrarian • React UI • {new Date().getFullYear()}
      </footer>
    </div>
  );
}
