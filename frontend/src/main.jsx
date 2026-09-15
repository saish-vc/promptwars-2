import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_URL?.trim() || "";

// Uniform SVG Lucide Icons
function FileTextIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <line x1="10" y1="9" x2="8" y2="9"/>
    </svg>
  );
}

function ShieldAlertIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  );
}

function GitCompareIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <circle cx="18" cy="18" r="3"/>
      <circle cx="6" cy="6" r="3"/>
      <path d="M13 6h3a2 2 0 0 1 2 2v7"/>
      <path d="M11 18H8a2 2 0 0 1-2-2V9"/>
    </svg>
  );
}

function CheckSquareIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <polyline points="9 11 12 14 22 4"/>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>
  );
}

function HandshakeIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="m11 17 2 2a1 1 0 0 0 1.4 0l4.3-4.3a1 1 0 0 0 0-1.4l-3-3"/>
      <path d="m14 14 2.5 2.5"/>
      <path d="m3 11 8-8 3 3-5 5"/>
      <path d="m15 5 4 4"/>
    </svg>
  );
}

function MessageSquareIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  );
}

function DownloadIcon({ className = "sidebar-icon" }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  );
}

function UploadCloudIcon({ className = "" }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
      <path d="M12 12v9"/>
      <path d="m16 16-4-4-4 4"/>
    </svg>
  );
}

function ClipboardIcon({ className = "" }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    </svg>
  );
}

function CheckIcon({ className = "" }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  );
}

const STEPS = [
  { id: "document", label: "Document", num: 1 },
  { id: "analysis", label: "Risk Audit", num: 2 },
  { id: "compare", label: "Compare", num: 3 },
  { id: "checklist", label: "Checklist", num: 4 },
  { id: "negotiation", label: "Strategy", num: 5 },
  { id: "chat", label: "Assistant", num: 6 },
  { id: "export", label: "Export Pack", num: 7 },
];

function App() {
  const [activeTab, setActiveTab] = useState("document");
  const [health, setHealth] = useState({ status: "Checking...", ok: false });

  // Document state
  const [textInput, setTextInput] = useState("");
  const [fileInput, setFileInput] = useState(null);
  const [currentDoc, setCurrentDoc] = useState(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState("");
  const [isDragActive, setIsDragActive] = useState(false);

  // Analysis state
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");

  // Comparison state
  const [docA, setDocA] = useState({ text: "", docId: "" });
  const [docB, setDocB] = useState({ text: "", docId: "" });
  const [userRole, setUserRole] = useState("Buyer");
  const [compareResult, setCompareResult] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState("");

  // Checklist state
  const [checklistResult, setChecklistResult] = useState(null);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const [checklistError, setChecklistError] = useState("");

  // Negotiation state
  const [selectedClause, setSelectedClause] = useState("");
  const [negotiationResult, setNegotiationResult] = useState(null);
  const [negotiationLoading, setNegotiationLoading] = useState(false);
  const [negotiationError, setNegotiationError] = useState("");

  // Chat state
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  // Export state
  const [exportContent, setExportContent] = useState("");
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState("");
  const [copiedToast, setCopiedToast] = useState(false);

  // Check health on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => setHealth({ status: data.status || "healthy", ok: true }))
      .catch(() => setHealth({ status: "Offline", ok: false }));
  }, []);

  // Sync default doc ID for comparison
  useEffect(() => {
    if (currentDoc?.doc_id && !docA.docId) {
      setDocA((prev) => ({ ...prev, docId: currentDoc.doc_id }));
    }
  }, [currentDoc]);

  // Handlers
  async function handlePasteDocument(e) {
    e.preventDefault();
    if (!textInput.trim()) return setDocError("Please enter contract text first.");
    setDocError("");
    setDocLoading(true);
    try {
      const res = await fetch(`${API_BASE}/documents/paste`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textInput }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Paste failed");
      setCurrentDoc(data);
    } catch (err) {
      setDocError(err.message);
    } finally {
      setDocLoading(false);
    }
  }

  async function handleUploadDocument(e) {
    e.preventDefault();
    if (!fileInput) return setDocError("Please select a file to upload.");
    setDocError("");
    setDocLoading(true);
    const body = new FormData();
    body.append("file", fileInput);
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setCurrentDoc(data);
    } catch (err) {
      setDocError(err.message);
    } finally {
      setDocLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!currentDoc?.doc_id) return setAnalysisError("Upload or paste a document first.");
    setAnalysisError("");
    setAnalysisLoading(true);
    try {
      const res = await fetch(`${API_BASE}/analyze/contract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: currentDoc.doc_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setAnalysisResult(data);
    } catch (err) {
      setAnalysisError(err.message);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleCompare(e) {
    e.preventDefault();
    setCompareError("");
    setCompareLoading(true);
    try {
      const payload = {
        document_a: docA.text ? { text: docA.text } : { doc_id: docA.docId },
        document_b: docB.text ? { text: docB.text } : { doc_id: docB.docId },
        user_role: userRole,
      };
      const res = await fetch(`${API_BASE}/compare/contracts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Comparison failed");
      setCompareResult(data);
    } catch (err) {
      setCompareError(err.message);
    } finally {
      setCompareLoading(false);
    }
  }

  async function handleGenerateChecklist() {
    if (!currentDoc?.doc_id) return setChecklistError("Upload or paste a document first.");
    setChecklistError("");
    setChecklistLoading(true);
    try {
      const res = await fetch(`${API_BASE}/generate/checklist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: currentDoc.doc_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Checklist generation failed");
      setChecklistResult(data);
    } catch (err) {
      setChecklistError(err.message);
    } finally {
      setChecklistLoading(false);
    }
  }

  async function handleGenerateNegotiation() {
    if (!currentDoc?.doc_id) return setNegotiationError("Upload or paste a document first.");
    setNegotiationError("");
    setNegotiationLoading(true);
    try {
      const res = await fetch(`${API_BASE}/generate/negotiation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: currentDoc.doc_id,
          clause_topic: selectedClause || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Negotiation strategy generation failed");
      setNegotiationResult(data);
    } catch (err) {
      setNegotiationError(err.message);
    } finally {
      setNegotiationLoading(false);
    }
  }

  async function handleSendChat(e) {
    e.preventDefault();
    const q = chatQuestion.trim();
    if (!q || !currentDoc?.doc_id) return;
    setChatError("");
    setChatQuestion("");
    setChatMessages((prev) => [...prev, { role: "user", text: q }]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat/contract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: currentDoc.doc_id, question: q }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat query failed");
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          confidence: data.confidence_score,
          sources: data.sources || [],
        },
      ]);
    } catch (err) {
      setChatError(err.message);
    } finally {
      setChatLoading(false);
    }
  }

  async function handleExportLawyerPack() {
    if (!currentDoc?.doc_id) return setExportError("Upload or paste a document first.");
    setExportError("");
    setExportLoading(true);
    try {
      const res = await fetch(`${API_BASE}/export/lawyer-pack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: currentDoc.doc_id,
          analysis: analysisResult,
          checklist: checklistResult,
          negotiation: negotiationResult,
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Export failed");
      }
      const text = await res.text();
      setExportContent(text);
    } catch (err) {
      setExportError(err.message);
    } finally {
      setExportLoading(false);
    }
  }

  function downloadExport() {
    const blob = new Blob([exportContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `LawyerPack_${currentDoc?.doc_id || "report"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function copyExport() {
    navigator.clipboard.writeText(exportContent);
    setCopiedToast(true);
    setTimeout(() => setCopiedToast(false), 2000);
  }

  const activeStepNum = STEPS.find((s) => s.id === activeTab)?.num || 1;

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <a href="#" className="brand-link">
          <div className="brand-logo-mark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="brand-title">LegiFlow</span>
          <span className="brand-tag">ENTERPRISE</span>
        </a>

        <div className="system-status-chip">
          <span className={`status-dot ${health.ok ? "ok" : "error"}`}></span>
          <span>System: {health.status}</span>
        </div>
      </header>

      <div className="main-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-nav-list">
            <div className="sidebar-section-label">Legal Audit Suite</div>

            <button
              className={`sidebar-nav-item ${activeTab === "document" ? "active" : ""}`}
              onClick={() => setActiveTab("document")}
            >
              <FileTextIcon /> 1. Document Ingestion
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "analysis" ? "active" : ""}`}
              onClick={() => setActiveTab("analysis")}
            >
              <ShieldAlertIcon /> 2. Risk & Clause Audit
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "compare" ? "active" : ""}`}
              onClick={() => setActiveTab("compare")}
            >
              <GitCompareIcon /> 3. Contract Comparison
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "checklist" ? "active" : ""}`}
              onClick={() => setActiveTab("checklist")}
            >
              <CheckSquareIcon /> 4. Compliance Checklist
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "negotiation" ? "active" : ""}`}
              onClick={() => setActiveTab("negotiation")}
            >
              <HandshakeIcon /> 5. Negotiation Playbook
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "chat" ? "active" : ""}`}
              onClick={() => setActiveTab("chat")}
            >
              <MessageSquareIcon /> 6. AI Legal Assistant
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "export" ? "active" : ""}`}
              onClick={() => setActiveTab("export")}
            >
              <DownloadIcon /> 7. Lawyer Pack Export
            </button>
          </div>

          {/* Active Document Status Card at Bottom */}
          <div className="sidebar-doc-card">
            <div className="sidebar-doc-header">
              <span className="sidebar-doc-title">Active Document</span>
              <span className={`sidebar-doc-badge ${currentDoc ? "loaded" : "empty"}`}>
                {currentDoc ? "Loaded" : "Empty"}
              </span>
            </div>
            <div className="sidebar-doc-id">
              {currentDoc ? `doc_${currentDoc.doc_id.slice(0, 12)}` : "No file loaded"}
            </div>
          </div>
        </aside>

        {/* Workspace */}
        <main className="content-workspace">
          {/* Top Horizontal Stepper */}
          <nav className="stepper-nav">
            {STEPS.map((step, idx) => {
              const isCompleted = step.num < activeStepNum;
              const isActive = activeTab === step.id;
              return (
                <React.Fragment key={step.id}>
                  <div
                    className={`stepper-node ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}
                    onClick={() => setActiveTab(step.id)}
                  >
                    <div className="stepper-circle">
                      {isCompleted ? <CheckIcon /> : step.num}
                    </div>
                    <span>{step.label}</span>
                  </div>
                  {idx < STEPS.length - 1 && <div className="stepper-line-divider"></div>}
                </React.Fragment>
              );
            })}
          </nav>

          {/* TAB 1: DOCUMENT INGESTION */}
          {activeTab === "document" && (
            <div className="dashboard-card">
              <header style={{ marginBottom: "24px" }}>
                <h1 className="page-title">Document Management</h1>
                <p className="caption-text">
                  Upload contract files or paste raw text to initiate automated clause extraction, liability analysis, and RAG indexing.
                </p>
              </header>

              {docError && <div className="alert-banner error">⚠️ {docError}</div>}
              {currentDoc && (
                <div className="alert-banner success">
                  ✅ Document Ingested Successfully — ID: <span style={{ fontFamily: "var(--font-mono)" }}>{currentDoc.doc_id}</span>
                </div>
              )}

              <div className="dual-panel-grid">
                {/* Upload File Panel */}
                <form onSubmit={handleUploadDocument} className="panel-box">
                  <div>
                    <header className="panel-box-header">
                      <h2 className="section-header" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <UploadCloudIcon /> Upload & Parse File
                      </h2>
                      <p className="caption-text">Select or drag a legal contract file for ingestion.</p>
                    </header>

                    <div
                      className={`dropzone-container ${isDragActive ? "drag-active" : ""}`}
                      onClick={() => document.getElementById("file-input-field").click()}
                      onDragOver={(e) => { e.preventDefault(); setIsDragActive(true); }}
                      onDragLeave={() => setIsDragActive(false)}
                      onDrop={(e) => {
                        e.preventDefault();
                        setIsDragActive(false);
                        if (e.dataTransfer.files?.[0]) setFileInput(e.dataTransfer.files[0]);
                      }}
                    >
                      <div className="dropzone-icon-circle">
                        <UploadCloudIcon />
                      </div>
                      <div>
                        <div className="dropzone-title">
                          {fileInput ? fileInput.name : "Click to select or drag file here"}
                        </div>
                        <div className="dropzone-hint">Max file size: 10MB</div>
                      </div>
                      <div className="file-tag-group">
                        <span className="file-tag-pill">.PDF</span>
                        <span className="file-tag-pill">.DOCX</span>
                        <span className="file-tag-pill">.TXT</span>
                      </div>
                    </div>

                    <input
                      id="file-input-field"
                      type="file"
                      style={{ display: "none" }}
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => setFileInput(e.target.files[0])}
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn-cta btn-cta-primary"
                    style={{ width: "100%", marginTop: "24px" }}
                    disabled={docLoading || !fileInput}
                  >
                    {docLoading ? <span className="micro-spinner"></span> : "Upload & Parse Document"}
                  </button>
                </form>

                {/* Paste Text Panel */}
                <form onSubmit={handlePasteDocument} className="panel-box">
                  <div>
                    <header className="panel-box-header">
                      <h2 className="section-header" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <ClipboardIcon /> Ingest Raw Text
                      </h2>
                      <p className="caption-text">Paste clause text directly for quick auditing.</p>
                    </header>

                    <textarea
                      className="input-textarea"
                      placeholder="Paste contract provisions, clauses, or agreement text..."
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                    ></textarea>
                  </div>

                  <button
                    type="submit"
                    className="btn-cta btn-cta-primary"
                    style={{ width: "100%", marginTop: "24px" }}
                    disabled={docLoading || !textInput.trim()}
                  >
                    {docLoading ? <span className="micro-spinner"></span> : "Ingest Text"}
                  </button>
                </form>
              </div>

              {currentDoc?.text_snippet && (
                <div style={{ marginTop: "24px" }}>
                  <h3 className="section-header">Parsed Document Preview</h3>
                  <pre className="monospace-block" style={{ maxHeight: "140px" }}>
                    {currentDoc.text_snippet}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: RISK AUDIT */}
          {activeTab === "analysis" && (
            <div className="dashboard-card">
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                <div>
                  <h1 className="page-title">Risk & Clause Audit</h1>
                  <p className="caption-text">Extract key indemnities, liabilities, and high-risk terms from the active document.</p>
                </div>
                <button className="btn-cta btn-cta-primary" onClick={handleAnalyze} disabled={analysisLoading || !currentDoc}>
                  {analysisLoading ? <span className="micro-spinner"></span> : "Run Risk Audit"}
                </button>
              </header>

              {analysisError && <div className="alert-banner error">⚠️ {analysisError}</div>}

              {analysisResult && (
                <div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "24px" }}>
                    <div className="panel-box">
                      <div className="caption-text">Document Type</div>
                      <div className="section-header" style={{ fontSize: "20px", marginTop: "4px" }}>{analysisResult.document_type || "General Agreement"}</div>
                    </div>
                    <div className="panel-box">
                      <div className="caption-text">Overall Risk Score</div>
                      <div className="section-header" style={{ fontSize: "20px", marginTop: "4px", color: analysisResult.risk_score > 70 ? "var(--color-danger)" : "var(--color-warning)" }}>
                        {analysisResult.risk_score} / 100
                      </div>
                    </div>
                    <div className="panel-box">
                      <div className="caption-text">Risk Items Identified</div>
                      <div className="section-header" style={{ fontSize: "20px", marginTop: "4px" }}>{analysisResult.risk_items?.length || 0}</div>
                    </div>
                  </div>

                  <div className="table-container">
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Severity</th>
                          <th>Category</th>
                          <th>Clause Quote</th>
                          <th>Risk Summary</th>
                          <th>Recommendation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisResult.risk_items?.map((item, idx) => (
                          <tr key={idx}>
                            <td>
                              <span style={{
                                padding: "2px 8px",
                                borderRadius: "9999px",
                                fontSize: "11px",
                                fontWeight: 600,
                                background: item.severity === "High" ? "rgba(240, 85, 90, 0.15)" : "rgba(245, 184, 77, 0.15)",
                                color: item.severity === "High" ? "var(--color-danger)" : "var(--color-warning)",
                                border: `1px solid ${item.severity === "High" ? "rgba(240, 85, 90, 0.3)" : "rgba(245, 184, 77, 0.3)"}`
                              }}>
                                {item.severity}
                              </span>
                            </td>
                            <td><strong>{item.category}</strong></td>
                            <td style={{ fontStyle: "italic", fontSize: "12px", color: "var(--text-secondary)" }}>"{item.clause_quote}"</td>
                            <td>{item.summary}</td>
                            <td>{item.recommendation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: CONTRACT COMPARISON */}
          {activeTab === "compare" && (
            <div className="dashboard-card">
              <header style={{ marginBottom: "24px" }}>
                <h1 className="page-title">Contract Comparison Matrix</h1>
                <p className="caption-text">Side-by-side clause comparison to detect imbalance and stance bias.</p>
              </header>

              {compareError && <div className="alert-banner error">⚠️ {compareError}</div>}

              <form onSubmit={handleCompare}>
                <div className="dual-panel-grid">
                  <div className="panel-box">
                    <header className="panel-box-header">
                      <h2 className="section-header">Document A (Baseline)</h2>
                    </header>
                    <input
                      type="text"
                      className="input-textarea"
                      style={{ minHeight: "40px", marginBottom: "12px" }}
                      placeholder="Doc ID (or paste text below)"
                      value={docA.docId}
                      onChange={(e) => setDocA({ ...docA, docId: e.target.value })}
                    />
                    <textarea
                      className="input-textarea"
                      placeholder="Paste baseline text..."
                      value={docA.text}
                      onChange={(e) => setDocA({ ...docA, text: e.target.value })}
                    ></textarea>
                  </div>

                  <div className="panel-box">
                    <header className="panel-box-header">
                      <h2 className="section-header">Document B (Counter-Proposal)</h2>
                    </header>
                    <input
                      type="text"
                      className="input-textarea"
                      style={{ minHeight: "40px", marginBottom: "12px" }}
                      placeholder="Doc ID (or paste text below)"
                      value={docB.docId}
                      onChange={(e) => setDocB({ ...docB, docId: e.target.value })}
                    />
                    <textarea
                      className="input-textarea"
                      placeholder="Paste counter-proposal text..."
                      value={docB.text}
                      onChange={(e) => setDocB({ ...docB, text: e.target.value })}
                    ></textarea>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "16px", alignItems: "center", marginTop: "24px" }}>
                  <label className="caption-text">Your Role:</label>
                  <select
                    className="input-textarea"
                    style={{ width: "auto", minHeight: "38px", padding: "4px 10px" }}
                    value={userRole}
                    onChange={(e) => setUserRole(e.target.value)}
                  >
                    <option value="Buyer">Buyer / Client</option>
                    <option value="Seller">Seller / Vendor</option>
                  </select>

                  <button type="submit" className="btn-cta btn-cta-primary" disabled={compareLoading}>
                    {compareLoading ? <span className="micro-spinner"></span> : "Compare Contracts"}
                  </button>
                </div>
              </form>

              {compareResult && (
                <div style={{ marginTop: "24px" }}>
                  <h3 className="section-header">Comparison Analysis</h3>
                  <p className="caption-text" style={{ marginBottom: "16px" }}>{compareResult.summary}</p>

                  <div className="table-container">
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Topic</th>
                          <th>Document A</th>
                          <th>Document B</th>
                          <th>Favors Stance</th>
                          <th>Explanation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {compareResult.diffs?.map((diff, idx) => (
                          <tr key={idx}>
                            <td><strong>{diff.topic}</strong></td>
                            <td style={{ fontSize: "12px" }}>{diff.text_a}</td>
                            <td style={{ fontSize: "12px" }}>{diff.text_b}</td>
                            <td>
                              <span style={{
                                padding: "2px 8px",
                                borderRadius: "9999px",
                                fontSize: "11px",
                                fontWeight: 600,
                                background: diff.favors === "Buyer" ? "rgba(91, 158, 240, 0.15)" : "rgba(108, 92, 231, 0.15)",
                                color: diff.favors === "Buyer" ? "var(--color-info)" : "#A29BFE"
                              }}>
                                {diff.favors || "Neutral"}
                              </span>
                            </td>
                            <td style={{ fontSize: "12px" }}>{diff.explanation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: CHECKLIST */}
          {activeTab === "checklist" && (
            <div className="dashboard-card">
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                <div>
                  <h1 className="page-title">Compliance Checklist</h1>
                  <p className="caption-text">Extract key operational requirements, deliverables, and tracking obligations.</p>
                </div>
                <button className="btn-cta btn-cta-primary" onClick={handleGenerateChecklist} disabled={checklistLoading || !currentDoc}>
                  {checklistLoading ? <span className="micro-spinner"></span> : "Generate Checklist"}
                </button>
              </header>

              {checklistError && <div className="alert-banner error">⚠️ {checklistError}</div>}

              {checklistResult && (
                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Category</th>
                        <th>Item</th>
                        <th>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {checklistResult.items?.map((item, idx) => (
                        <tr key={idx}>
                          <td>
                            <span style={{
                              padding: "2px 8px",
                              borderRadius: "9999px",
                              fontSize: "11px",
                              fontWeight: 600,
                              background: item.status === "Pass" ? "rgba(61, 214, 140, 0.15)" : "rgba(240, 85, 90, 0.15)",
                              color: item.status === "Pass" ? "var(--color-success)" : "var(--color-danger)"
                            }}>
                              {item.status}
                            </span>
                          </td>
                          <td><strong>{item.category}</strong></td>
                          <td>{item.item}</td>
                          <td>{item.details}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: NEGOTIATION */}
          {activeTab === "negotiation" && (
            <div className="dashboard-card">
              <header style={{ marginBottom: "24px" }}>
                <h1 className="page-title">Negotiation Playbook</h1>
                <p className="caption-text">Generate target counter-proposals, fallback clauses, and walk-away points.</p>
              </header>

              {negotiationError && <div className="alert-banner error">⚠️ {negotiationError}</div>}

              <div style={{ display: "flex", gap: "16px", marginBottom: "24px" }}>
                <input
                  type="text"
                  className="input-textarea"
                  style={{ minHeight: "38px", maxWidth: "340px" }}
                  placeholder="Focus Clause Topic (Optional)"
                  value={selectedClause}
                  onChange={(e) => setSelectedClause(e.target.value)}
                />
                <button className="btn-cta btn-cta-primary" onClick={handleGenerateNegotiation} disabled={negotiationLoading || !currentDoc}>
                  {negotiationLoading ? <span className="micro-spinner"></span> : "Generate Playbook"}
                </button>
              </div>

              {negotiationResult && (
                <div style={{ display: "grid", gap: "16px" }}>
                  {negotiationResult.strategies?.map((item, idx) => (
                    <div key={idx} className="panel-box">
                      <h3 className="section-header" style={{ color: "var(--accent-primary)" }}>{item.clause_name}</h3>
                      <p className="caption-text" style={{ fontStyle: "italic", marginTop: "4px" }}>
                        Current Text: "{item.current_text}"
                      </p>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px", marginTop: "16px" }}>
                        <div>
                          <strong style={{ color: "var(--color-success)", fontSize: "11px", textTransform: "uppercase" }}>🎯 TARGET POSITION</strong>
                          <p style={{ fontSize: "13px", marginTop: "4px" }}>{item.target_position}</p>
                        </div>
                        <div>
                          <strong style={{ color: "var(--color-warning)", fontSize: "11px", textTransform: "uppercase" }}>🛡️ FALLBACK POSITION</strong>
                          <p style={{ fontSize: "13px", marginTop: "4px" }}>{item.fallback_position}</p>
                        </div>
                        <div>
                          <strong style={{ color: "var(--color-danger)", fontSize: "11px", textTransform: "uppercase" }}>🚫 WALK-AWAY POINT</strong>
                          <p style={{ fontSize: "13px", marginTop: "4px" }}>{item.walkaway_point}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 6: CHAT */}
          {activeTab === "chat" && (
            <div className="dashboard-card">
              <header style={{ marginBottom: "24px" }}>
                <h1 className="page-title">AI Legal Assistant</h1>
                <p className="caption-text">Ask context-aware questions about the contract with cited RAG responses.</p>
              </header>

              {chatError && <div className="alert-banner error">⚠️ {chatError}</div>}

              <div className="panel-box" style={{ height: "420px", display: "flex", flexDirection: "column" }}>
                <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px", marginBottom: "16px" }}>
                  {chatMessages.length === 0 ? (
                    <div style={{ textAlign: "center", color: "var(--text-disabled)", margin: "auto" }}>
                      💡 Ask any question about the contract text...
                    </div>
                  ) : (
                    chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        style={{
                          alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                          maxWidth: "80%",
                          padding: "10px 14px",
                          borderRadius: "12px",
                          fontSize: "13px",
                          background: msg.role === "user" ? "rgba(108, 92, 231, 0.2)" : "var(--bg-card-elevated)",
                          border: `1px solid ${msg.role === "user" ? "rgba(108, 92, 231, 0.4)" : "var(--border-card)"}`,
                          color: "var(--text-primary)"
                        }}
                      >
                        {msg.text}
                      </div>
                    ))
                  )}
                  {chatLoading && <div style={{ color: "var(--text-secondary)", fontSize: "13px" }}>Searching contract provisions...</div>}
                </div>

                <form onSubmit={handleSendChat} style={{ display: "flex", gap: "12px" }}>
                  <input
                    type="text"
                    className="input-textarea"
                    style={{ minHeight: "40px", flex: 1 }}
                    placeholder="Ask a question..."
                    value={chatQuestion}
                    onChange={(e) => setChatQuestion(e.target.value)}
                    disabled={chatLoading || !currentDoc}
                  />
                  <button type="submit" className="btn-cta btn-cta-primary" disabled={chatLoading || !currentDoc}>
                    Send
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 7: EXPORT */}
          {activeTab === "export" && (
            <div className="dashboard-card">
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                <div>
                  <h1 className="page-title">Lawyer Pack Export</h1>
                  <p className="caption-text">Compile risk audit, compliance items, and negotiation playbooks into a executive report.</p>
                </div>
                {/* Hero CTA Accent Reserved Specifically for LawyerPack Report Generation */}
                <button className="btn-cta btn-cta-hero" onClick={handleExportLawyerPack} disabled={exportLoading || !currentDoc}>
                  {exportLoading ? <span className="micro-spinner"></span> : "Compile Lawyer Pack Report"}
                </button>
              </header>

              {exportError && <div className="alert-banner error">⚠️ {exportError}</div>}
              {copiedToast && <div className="alert-banner success">📋 Copied to clipboard!</div>}

              {exportContent && (
                <div>
                  <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
                    <button className="btn-cta btn-cta-secondary" onClick={copyExport}>📋 Copy Text</button>
                    <button className="btn-cta btn-cta-hero" onClick={downloadExport}>⬇️ Download .txt</button>
                  </div>
                  <pre className="monospace-block">{exportContent}</pre>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);
  root.render(<App />);
}
