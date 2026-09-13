import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const api = import.meta.env.VITE_API_URL || "";

function App() {
  const [health, setHealth] = useState("Checking backend…");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${api}/health`)
      .then((response) => response.json())
      .then(({ status }) => setHealth(`Backend: ${status}`))
      .catch(() => setHealth("Backend unavailable"));
  }, []);

  async function ingest(endpoint, options) {
    setError("");
    setResult(null);
    const response = await fetch(`${api}${endpoint}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Upload failed");
    setResult(data);
  }

  async function paste(event) {
    event.preventDefault();
    try {
      await ingest("/documents/paste", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
    } catch (reason) { setError(reason.message); }
  }

  async function upload(event) {
    event.preventDefault();
    if (!file) return setError("Choose a PDF, DOCX, or TXT file.");
    const body = new FormData();
    body.append("file", file);
    try { await ingest("/documents/upload", { method: "POST", body }); } catch (reason) { setError(reason.message); }
  }

  return <main><h1>LegiFlow</h1><p>General legal information, not legal advice.</p><p>{health}</p>
    <section><h2>Add a document</h2><form onSubmit={paste}><textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste contract text" required /><button>Save pasted text</button></form>
    <form onSubmit={upload}><input type="file" accept=".pdf,.docx,.txt" onChange={(event) => setFile(event.target.files[0])} /><button>Upload file</button></form></section>
    {error && <p role="alert">{error}</p>}{result && <section><strong>Document ID: {result.doc_id}</strong><pre>{result.text}</pre></section>}</main>;
}

createRoot(document.getElementById("root")).render(<App />);
