import { useMemo, useState } from "react";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:2050";

type ChatResponse = {
  answer: string;
  chosen_title?: string;
  summary?: string;
};

type ImageResponse = { image_url: string };
type TTSResponse = { audio_url: string };
type STTResponse = { text: string };

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export default function App() {
  // core chat state
  const [userQ, setUserQ] = useState("");                     // user input text
  const [answer, setAnswer] = useState("");                   // assistant's answer text
  const [chosenTitle, setChosenTitle] = useState<string>();   // which book was selected
  const [summary, setSummary] = useState<string>();           // summary text for chosen book

  // media URLs
  const [imageUrl, setImageUrl] = useState<string>();         // generated image URL
  const [audioUrl, setAudioUrl] = useState<string>();         // generated audio URL

  // loading flags + errors
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadingImage, setLoadingImage] = useState(false);
  const [loadingTTS, setLoadingTTS] = useState(false);
  const [loadingSTT, setLoadingSTT] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // STT recording state
  const [recorder, setRecorder] = useState<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);

  // derived flags to enable/disable action buttons
  const canGenImage = useMemo(() => !!chosenTitle && !!summary, [chosenTitle, summary]);
  const canTTS = useMemo(() => answer.trim().length > 0, [answer]);

  /** send user's question to /api/chat */
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

  /** generate image for chosen title */
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
      setImageUrl(`${BASE_URL}${res.image_url}`);
    } catch (e: any) {
      setError(e.message || "Image generation failed");
    } finally {
      setLoadingImage(false);
    }
  }

  /** TTS for assistant answer */
  async function onTTS() {
    if (!canTTS) return;
    setLoadingTTS(true);
    setError(null);
    setAudioUrl(undefined);
    try {
      const res = await postJSON<TTSResponse>("/api/tts", { text: answer });
      setAudioUrl(`${BASE_URL}${res.audio_url}`);
    } catch (e: any) {
      setError(e.message || "TTS failed");
    } finally {
      setLoadingTTS(false);
    }
  }

   /** STT via microphone recording using MediaRecorder. */
  async function startRecording() {
    setError(null);

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone access not supported in this browser.");
      return;
    }

    const preferredTypes = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg",
    ];
    let mimeType = "";
    for (const t of preferredTypes) {
      if ((window as any).MediaRecorder && MediaRecorder.isTypeSupported(t)) {
        mimeType = t;
        break;
      }
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      const chunks: BlobPart[] = [];

      mr.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(chunks, { type: mimeType || "audio/webm" });

        const mt = mimeType || "";
        const ext = mt.includes("mp4") ? "m4a" : mt.includes("ogg") ? "ogg" : "webm";

        setLoadingSTT(true);
        try {
          const form = new FormData();
          form.append("file", blob, `recording.${ext}`);
          form.append("language", "ro");
          const res = await postForm<STTResponse>("/api/stt", form);

          const text = (res.text || "").trim();
          setUserQ(text);
        } catch (e: any) {
          setError(e.message || "STT failed");
        } finally {
          setLoadingSTT(false);
        }

        stream.getTracks().forEach((t) => t.stop());
        setRecorder(null);
      };

      mr.start();
      setRecorder(mr);
      setRecording(true);
    } catch (err: any) {
      setError(err?.message || "Could not access microphone.");
    }
  }

  function stopRecording() {
    try {
      recorder?.stop();
    } finally {
      setRecording(false);
    }
  }

  // the rendering part
  return (
    <div className="min-h-screen">
      <header className="container header">
        <h1 className="h1">Smart Librarian</h1>
        <p className="subtle">
          RAG + LLM book recommendations • image generation • speech I/O
        </p>
      </header>

      <main className="container" style={{ paddingBottom: "6rem" }}>
        {/* Query box */}
        <section className="panel">
          <label className="block text-sm font-medium mb-2">Întreabă-mă ceva:</label>
          <textarea
            className="textarea"
            rows={3}
            placeholder='Ex: „Vreau o carte despre prietenie.”'
            value={userQ}
            onChange={(e) => setUserQ(e.target.value)}
          />
          <div className="row" style={{ alignItems: "center", gap: ".5rem", flexWrap: "wrap" }}>
            <button
              onClick={onSend}
              disabled={loadingChat}
              className="btn btn-blue"
            >
              {loadingChat ? "Thinking…" : "Ask"}
            </button>

            {/* STT mic controls */}
            <button
              type="button"
              disabled={loadingSTT}
              onClick={() => (recording ? stopRecording() : startRecording())}
              className="btn btn-outline"
            >
              {recording ? "⏹️ Stop" : "🎙️ Record input prompt"}
            </button>
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

            {/* Answer + summary */}
            <div className="answer">
              {answer}
              {summary ? `\n\nSumar:\n${summary}` : ""}
            </div>

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
