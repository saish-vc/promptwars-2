import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const api = import.meta.env.VITE_API_URL?.trim() || "";

function App() {
  const [health, setHealth] = useState("Checking backend…");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // comparison state
  const [docA, setDocA] = useState({ text: "", file: null });
  const [docB, setDocB] = useState({ text: "", file: null });
  const [userRole, setUserRole] = useState("Buyer");
  const [compareResult, setCompareResult] = useState(null);
  const [compareError, setCompareError] = useState("");

  useEffect(() => {
    if (!api) {
      setHealth("Backend URL is not configured");
      return;
    }
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

  async function compare(event) {
    event.preventDefault();
    setCompareError("");
    setCompareResult(null);
    try {
      const payload = {
        document_a: docA.text ? { text: docA.text } : { doc_id: docA.docId },
        document_b: docB.text ? { text: docB.text } : { doc_id: docB.docId },
        user_role: userRole,
      };
      const response = await fetch(`${api}/compare/contracts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Comparison failed");
      setCompareResult(data);
    } catch (reason) {
      setCompareError(reason.message);
    }
  }

  function setDocAId(docId) {
    setDocA((prev) => ({ ...prev, docId }));
  }
  function setDocBId(docId) {
    setDocB((prev) => ({ ...prev, docId }));
  }

  function favorsBadge(favors) {
    const label = favors === "seller" ? "Seller" : favors === "buyer" ? "Buyer" : "Neutral";
    const cls = favors === "seller" ? "badge-seller" : favors === "buyer" ? "badge-buyer" : "badge-neutral";
    return <span className={`badge ${cls}`}>{label}</span>;
  }

  return (
    <main>
      <h1>LegiFlow</h1>
      <p>General legal information, not legal advice.</p>
      <p>{health}</p>

      <section>
        <h2>Add a document</h2>
        <form onSubmit={paste}>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Paste contract text"
            required
          />
          <button>Save pasted text</button>
        </form>
        <form onSubmit={upload}>
          <input type="file" accept=".pdf,.docx,.txt" onChange={(event) => setFile(event.target.files[0])} />
          <button>Upload file</button>
        </form>
      </section>

      <section>
        <h2>Compare two contracts</h2>
        <div className="compare-grid">
          <div className="compare-col">
            <h3>Version A</h3>
            <form onSubmit={(e) => { e.preventDefault(); setDocAId(result?.doc_id || ""); }}>
              <button type="submit" disabled={!result?.doc_id}>Use last uploaded doc as A</button>
            </form>
            <textarea
              value={docA.text}
              onChange={(e) => setDocA((p) => ({ ...p, text: e.target.value }))}
              placeholder="Paste Version A text"
            />
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => {
                const f = e.target.files[0];
                if (!f) return;
                const body = new FormData();
                body.append("file", f);
                fetch(`${api}/documents/upload`, { method: "POST", body }).then((r) => r.json()).then((d) => setDocAId(d.doc_id)).catch((err) => setCompareError(err.message));
              }}
            />
          </div>
          <div className="compare-col">
            <h3>Version B</h3>
            <form onSubmit={(e) => { e.preventDefault(); setDocBId(result?.doc_id || ""); }}>
              <button type="submit" disabled={!result?.doc_id}>Use last uploaded doc as B</button>
            </form>
            <textarea
              value={docB.text}
              onChange={(e) => setDocB((p) => ({ ...p, text: e.target.value }))}
              placeholder="Paste Version B text"
            />
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => {
                const f = e.target.files[0];
                if (!f) return;
                const body = new FormData();
                body.append("file", f);
                fetch(`${api}/documents/upload`, { method: "POST", body }).then((r) => r.json()).then((d) => setDocBId(d.doc_id)).catch((err) => setCompareError(err.message));
              }}
            />
          </div>
        </div>
        <div className="compare-controls">
          <label>
            I represent:
            <select value={userRole} onChange={(e) => setUserRole(e.target.value)}>
              <option>Buyer</option>
              <option>Seller</option>
              <option>Landlord</option>
              <option>Tenant</option>
              <option>Employer</option>
              <option>Employee</option>
            </select>
          </label>
          <button onClick={compare}>Compare</button>
        </div>
      </section>

      {compareError && <p role="alert">{compareError}</p>}
      {compareResult && (
        <section>
          <h2>Differences</h2>
          <p>{compareResult.summary}</p>
          <table className="diff-table">
            <thead>
              <tr>
                <th>Clause</th>
                <th>Version A</th>
                <th>Version B</th>
                <th>Favors</th>
                <th>Why</th>
                <th>What it means for you</th>
              </tr>
            </thead>
            <tbody>
              {compareResult.differences.map((diff, i) => (
                <tr key={i}>
                  <td>{diff.clause}</td>
                  <td>{diff.in_a}</td>
                  <td>{diff.in_b}</td>
                  <td>{favorsBadge(diff.favors)}</td>
                  <td>{diff.reason}</td>
                  <td>{diff.context_for_role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {error && <p role="alert">{error}</p>}
      {result && (
        <section>
          <strong>Document ID: {result.doc_id}</strong>
          <pre>{result.text}</pre>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
