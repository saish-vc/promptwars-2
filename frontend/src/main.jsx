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

  // analysis state
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  // checklist state
  const [checklistResult, setChecklistResult] = useState(null);
  const [checklistError, setChecklistError] = useState("");

  // negotiation state
  const [negotiationResult, setNegotiationResult] = useState(null);
  const [negotiationError, setNegotiationError] = useState("");
  const [selectedClause, setSelectedClause] = useState("");

  // chat state
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatError, setChatError] = useState("");

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

  async function analyze() {
    setAnalysisError("");
    setAnalysisResult(null);
    try {
      const response = await fetch(`${api}/analyze/document`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: result?.text || text }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Analysis failed");
      setAnalysisResult(data);
    } catch (reason) {
      setAnalysisError(reason.message);
    }
  }

  async function generateChecklist() {
    setChecklistError("");
    setChecklistResult(null);
    try {
      const response = await fetch(`${api}/generate/checklist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: result?.text || text,
          analysis: analysisResult,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Checklist generation failed");
      setChecklistResult(data);
    } catch (reason) {
      setChecklistError(reason.message);
    }
  }

  async function generateNegotiation(clauseTitle, clauseText) {
    setNegotiationError("");
    setNegotiationResult(null);
    try {
      const response = await fetch(`${api}/generate/negotiation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: result?.text || text,
          analysis: analysisResult,
          clause_title: clauseTitle,
          clause_text: clauseText,
          user_role: userRole,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Negotiation generation failed");
      setNegotiationResult(data);
    } catch (reason) {
      setNegotiationError(reason.message);
    }
  }

  async function sendChatMessage() {
    if (!chatQuestion.trim() || !result?.doc_id) return;
    setChatError("");
    const userMessage = { role: "user", text: chatQuestion };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatQuestion("");
    
    try {
      const response = await fetch(`${api}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: result.doc_id,
          question: chatQuestion,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Chat failed");
      setChatMessages((prev) => [...prev, { role: "assistant", ...data }]);
    } catch (reason) {
      setChatError(reason.message);
      setChatMessages((prev) => [...prev, { role: "error", text: reason.message }]);
    }
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

      <section>
        <h2>Analyze document</h2>
        <button onClick={analyze} disabled={!result?.text && !text}>Analyze current document</button>
        {analysisError && <p role="alert">{analysisError}</p>}
        {analysisResult && (
          <div>
            <h3>Analysis Results</h3>
            <p><strong>Summary:</strong> {analysisResult.summary}</p>
            <p><strong>Parties:</strong> {analysisResult.parties?.join(", ")}</p>
            <h4>Risk Clauses</h4>
            <ul>
              {analysisResult.risk_clauses?.map((clause, i) => (
                <li key={i}>
                  <strong>{clause.title}</strong> (Score: {clause.score}) - {clause.reason}
                </li>
              ))}
            </ul>
            <button onClick={generateChecklist}>Generate Checklist</button>
          </div>
        )}
      </section>

      {checklistError && <p role="alert">{checklistError}</p>}
      {checklistResult && (
        <section>
          <h2>Checklist & Lawyer Questions</h2>
          <h3>Checklist</h3>
          <ul>
            {checklistResult.checklist?.map((item, i) => (
              <li key={i}>{item.item} ({item.status})</li>
            ))}
          </ul>
          <h3>Questions for Lawyer</h3>
          <ul>
            {checklistResult.lawyer_questions?.map((q, i) => (
              <li key={i}>
                <strong>{q.question}</strong> - Context: {q.context}
              </li>
            ))}
          </ul>
        </section>
      )}

      {analysisResult && (
        <section>
          <h2>Negotiation Assistance</h2>
          <label>
            Select risky clause to negotiate:
            <select value={selectedClause} onChange={(e) => setSelectedClause(e.target.value)}>
              <option value="">-- Select a clause --</option>
              {analysisResult.risk_clauses?.map((clause, i) => (
                <option key={i} value={clause.title}>{clause.title} (Score: {clause.score})</option>
              ))}
            </select>
          </label>
          <button 
            onClick={() => {
              const clause = analysisResult.risk_clauses?.find(c => c.title === selectedClause);
              if (clause) generateNegotiation(clause.title, clause.title + ": " + clause.reason);
            }}
            disabled={!selectedClause}
          >
            Generate Negotiation Points
          </button>
          {negotiationError && <p role="alert">{negotiationError}</p>}
          {negotiationResult && (
            <div>
              <h3>Counter Clause</h3>
              <p>{negotiationResult.counter_clause}</p>
              <h3>Talking Points</h3>
              <ul>
                {negotiationResult.talking_points?.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {result?.doc_id && (
        <section>
          <h2>Ask about this contract</h2>
          <div className="chat-container">
            <div className="chat-messages">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`chat-message ${msg.role}`}>
                  {msg.role === "assistant" ? (
                    <div>
                      <p>{msg.answer}</p>
                      <p className="confidence">Confidence: {Math.round(msg.confidence * 100)}%</p>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="sources">
                          <strong>Sources:</strong>
                          <ul>
                            {msg.sources.map((source, j) => (
                              <li key={j}>"{source.text}"</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p>{msg.text}</p>
                  )}
                </div>
              ))}
            </div>
            <form onSubmit={(e) => { e.preventDefault(); sendChatMessage(); }}>
              <input
                type="text"
                value={chatQuestion}
                onChange={(e) => setChatQuestion(e.target.value)}
                placeholder="Ask a question about this contract..."
                disabled={!result?.doc_id}
              />
              <button type="submit" disabled={!chatQuestion.trim() || !result?.doc_id}>Send</button>
            </form>
            {chatError && <p role="alert">{chatError}</p>}
          </div>
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
