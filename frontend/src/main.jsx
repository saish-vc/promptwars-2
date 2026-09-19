import React, { useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_URL?.trim() || "";

// Uniform SVG Lucide Icons with aria-hidden
function FileTextIcon({ className = "sidebar-icon" }) {
  return (
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
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
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  );
}

function GitCompareIcon({ className = "sidebar-icon" }) {
  return (
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <circle cx="18" cy="18" r="3"/>
      <circle cx="6" cy="6" r="3"/>
      <path d="M13 6h3a2 2 0 0 1 2 2v7"/>
      <path d="M11 18H8a2 2 0 0 1-2-2V9"/>
    </svg>
  );
}

function CheckSquareIcon({ className = "sidebar-icon" }) {
  return (
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <polyline points="9 11 12 14 22 4"/>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>
  );
}

function HandshakeIcon({ className = "sidebar-icon" }) {
  return (
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="m11 17 2 2a1 1 0 0 0 1.4 0l4.3-4.3a1 1 0 0 0 0-1.4l-3-3"/>
      <path d="m14 14 2.5 2.5"/>
      <path d="m3 11 8-8 3 3-5 5"/>
      <path d="m15 5 4 4"/>
    </svg>
  );
}

function MessageSquareIcon({ className = "sidebar-icon" }) {
  return (
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  );
}

function DownloadIcon({ className = "sidebar-icon" }) {
  return (
    <svg aria-hidden="true" className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  );
}

function UploadCloudIcon({ className = "" }) {
  return (
    <svg aria-hidden="true" className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
      <path d="M12 12v9"/>
      <path d="m16 16-4-4-4 4"/>
    </svg>
  );
}

function ClipboardIcon({ className = "" }) {
  return (
    <svg aria-hidden="true" className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    </svg>
  );
}

function CheckIcon({ className = "" }) {
  return (
    <svg aria-hidden="true" className={className} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
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
  const [announcement, setAnnouncement] = useState("");

  // Accessibility Toolbar State
  const [isHighContrast, setIsHighContrast] = useState(false);
  const [fontSize, setFontSize] = useState("normal");

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

  // Screen reader announcer helper
  function announce(message) {
    setAnnouncement(message);
  }

  // Sync Accessibility Classes to <body>
  useEffect(() => {
    if (isHighContrast) {
      document.body.classList.add("high-contrast");
    } else {
      document.body.classList.remove("high-contrast");
    }
  }, [isHighContrast]);

  useEffect(() => {
    document.body.classList.remove("font-large", "font-xlarge");
    if (fontSize === "large") document.body.classList.add("font-large");
    if (fontSize === "xlarge") document.body.classList.add("font-xlarge");
  }, [fontSize]);

  // Check health on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => {
        setHealth({ status: data.status || "healthy", ok: true });
        announce("Connected to backend server.");
      })
      .catch(() => {
        setHealth({ status: "Offline", ok: false });
        announce("Backend server is offline.");
      });
  }, []);

  // Sync default doc ID for comparison
  useEffect(() => {
    if (currentDoc?.doc_id && !docA.docId) {
      setDocA((prev) => ({ ...prev, docId: currentDoc.doc_id }));
    }
  }, [currentDoc]);

  // Keyboard navigation for tablist
  function handleTabKeyDown(e, currentId) {
    const currentIndex = STEPS.findIndex((s) => s.id === currentId);
    let nextIndex = currentIndex;
    if (e.key === "ArrowRight") {
      nextIndex = (currentIndex + 1) % STEPS.length;
    } else if (e.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + STEPS.length) % STEPS.length;
    } else if (e.key === "Home") {
      nextIndex = 0;
    } else if (e.key === "End") {
      nextIndex = STEPS.length - 1;
    } else {
      return;
    }
    e.preventDefault();
    const nextStep = STEPS[nextIndex];
    setActiveTab(nextStep.id);
    announce(`Navigated to ${nextStep.label} tab.`);
    const nextEl = document.getElementById(`tab-${nextStep.id}`);
    if (nextEl) nextEl.focus();
  }

  function handleTabSelect(id) {
    setActiveTab(id);
    const step = STEPS.find((s) => s.id === id);
    announce(`Switched to ${step?.label || id} view.`);
  }

  // Handlers
  async function handlePasteDocument(e) {
    e.preventDefault();
    if (!textInput.trim()) return setDocError("Please enter contract text first.");
    setDocError("");
    setDocLoading(true);
    announce("Processing pasted document text...");
    try {
      const res = await fetch(`${API_BASE}/documents/paste`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textInput }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Paste failed");
      setCurrentDoc(data);
      announce(`Document processed successfully. Document ID assigned.`);
    } catch (err) {
      setDocError(err.message);
      announce(`Error: ${err.message}`);
    } finally {
      setDocLoading(false);
    }
  }

  async function handleUploadDocument(e) {
    e.preventDefault();
    if (!fileInput) return setDocError("Please select a file to upload.");
    setDocError("");
    setDocLoading(true);
    announce(`Uploading file ${fileInput.name}...`);
    const body = new FormData();
    body.append("file", fileInput);
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body,
      });
      const data = await res.json().catch(() => {
        throw new Error(
          "The upload server returned a non-JSON response. Set VITE_API_URL to the deployed backend URL."
        );
      });
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setCurrentDoc(data);
      announce(`File ${fileInput.name} uploaded and parsed successfully.`);
    } catch (err) {
      setDocError(err.message);
      announce(`Upload failed: ${err.message}`);
    } finally {
      setDocLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!currentDoc?.doc_id) return setAnalysisError("Upload or paste a document first.");
    setAnalysisError("");
    setAnalysisLoading(true);
    announce("Performing AI risk audit and clause scoring...");
    try {
      const res = await fetch(`${API_BASE}/analyze/contract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: currentDoc.doc_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setAnalysisResult(data);
      announce("Risk audit completed successfully.");
    } catch (err) {
      setAnalysisError(err.message);
      announce(`Analysis error: ${err.message}`);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleCompare(e) {
    e.preventDefault();
    setCompareError("");
    setCompareLoading(true);
    announce("Comparing contracts...");
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
      announce("Contract comparison complete.");
    } catch (err) {
      setCompareError(err.message);
      announce(`Comparison error: ${err.message}`);
    } finally {
      setCompareLoading(false);
    }
  }

  async function handleGenerateChecklist() {
    if (!currentDoc?.doc_id) return setChecklistError("Upload or paste a document first.");
    setChecklistError("");
    setChecklistLoading(true);
    announce("Generating compliance checklist and lawyer questions...");
    try {
      const res = await fetch(`${API_BASE}/generate/checklist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: currentDoc.doc_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Checklist generation failed");
      setChecklistResult(data);
      announce("Checklist generated successfully.");
    } catch (err) {
      setChecklistError(err.message);
      announce(`Checklist error: ${err.message}`);
    } finally {
      setChecklistLoading(false);
    }
  }

  async function handleGenerateNegotiation() {
    if (!currentDoc?.doc_id) return setNegotiationError("Upload or paste a document first.");
    setNegotiationError("");
    setNegotiationLoading(true);
    announce("Generating negotiation strategy and counter-clause...");
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
      announce("Negotiation strategy generated.");
    } catch (err) {
      setNegotiationError(err.message);
      announce(`Negotiation error: ${err.message}`);
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
    announce(`Sending question to AI legal assistant: ${q}`);
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
          confidence: data.confidence_score || data.confidence,
          sources: data.sources || [],
        },
      ]);
      announce("AI legal assistant answered your question.");
    } catch (err) {
      setChatError(err.message);
      announce(`Chat error: ${err.message}`);
    } finally {
      setChatLoading(false);
    }
  }

  async function handleExportLawyerPack() {
    if (!currentDoc?.doc_id) return setExportError("Upload or paste a document first.");
    setExportError("");
    setExportLoading(true);
    announce("Generating comprehensive Lawyer Pack export...");
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
      announce("Lawyer Pack generated successfully.");
    } catch (err) {
      setExportError(err.message);
      announce(`Export error: ${err.message}`);
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
    announce("Lawyer Pack downloaded as text file.");
  }

  function copyExport() {
    navigator.clipboard.writeText(exportContent);
    setCopiedToast(true);
    announce("Copied Lawyer Pack report to clipboard.");
    setTimeout(() => setCopiedToast(false), 2000);
  }

  const activeStepNum = STEPS.find((s) => s.id === activeTab)?.num || 1;

  return (
    <div className="app-container">
      {/* Accessibility Skip Link */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Screen Reader Live Announcement Region */}
      <div role="status" aria-live="polite" className="sr-only">
        {announcement}
      </div>

      {/* Top Navbar */}
      <header className="navbar" role="banner">
        <a href="#" className="brand-link" aria-label="LegiFlow Homepage">
          <div className="brand-logo-mark" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="brand-title">LegiFlow</span>
          <span className="brand-tag">ENTERPRISE</span>
        </a>

        {/* Accessibility Toolbar */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div role="group" aria-label="Accessibility options" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ padding: "4px 10px", fontSize: "12px" }}
              onClick={() => {
                setIsHighContrast(!isHighContrast);
                announce(isHighContrast ? "High Contrast Mode Disabled" : "High Contrast Mode Enabled");
              }}
              aria-pressed={isHighContrast}
              aria-label="Toggle High Contrast Mode"
            >
              👁️ {isHighContrast ? "Contrast: ON" : "Contrast: OFF"}
            </button>

            <select
              aria-label="Select Font Size"
              className="btn-secondary"
              style={{ padding: "4px 8px", fontSize: "12px", background: "var(--bg-card)" }}
              value={fontSize}
              onChange={(e) => {
                setFontSize(e.target.value);
                announce(`Font size changed to ${e.target.value}`);
              }}
            >
              <option value="normal">Font: Normal</option>
              <option value="large">Font: Large</option>
              <option value="xlarge">Font: Extra Large</option>
            </select>
          </div>

          <div className="system-status-chip" role="status" aria-label={`System status: ${health.status}`}>
            <span className={`status-dot ${health.ok ? "ok" : "error"}`}></span>
            <span>System: {health.status}</span>
          </div>
        </div>
      </header>

      <div className="main-layout">
        {/* Sidebar Navigation */}
        <nav className="sidebar" aria-label="Main workflow sidebar navigation">
          <div role="tablist" aria-label="Legal Audit Workflow Steps" className="sidebar-nav-list">
            <div className="sidebar-section-label" id="sidebar-label">Legal Audit Suite</div>

            {STEPS.map((step) => {
              const isActive = activeTab === step.id;
              const IconComp = 
                step.id === "document" ? FileTextIcon :
                step.id === "analysis" ? ShieldAlertIcon :
                step.id === "compare" ? GitCompareIcon :
                step.id === "checklist" ? CheckSquareIcon :
                step.id === "negotiation" ? HandshakeIcon :
                step.id === "chat" ? MessageSquareIcon : DownloadIcon;

              return (
                <button
                  key={step.id}
                  role="tab"
                  id={`tab-${step.id}`}
                  aria-selected={isActive}
                  aria-controls={`panel-${step.id}`}
                  tabIndex={isActive ? 0 : -1}
                  className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                  onKeyDown={(e) => handleTabKeyDown(e, step.id)}
                  onClick={() => handleTabSelect(step.id)}
                >
                  <IconComp /> {step.num}. {step.label}
                </button>
              );
            })}
          </div>

          {/* Active Document Status Card */}
          <div className="sidebar-doc-card" role="region" aria-label="Active Loaded Document">
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
        </nav>

        {/* Main Workspace */}
        <main id="main-content" tabIndex="-1" className="content-workspace">
          {/* Horizontal Stepper Indicator */}
          <nav className="stepper-nav" aria-label="Workflow progress stepper">
            {STEPS.map((step, idx) => {
              const isCompleted = step.num < activeStepNum;
              const isActive = activeTab === step.id;
              return (
                <React.Fragment key={step.id}>
                  <div
                    className={`stepper-node ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}
                    onClick={() => handleTabSelect(step.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && handleTabSelect(step.id)}
                    aria-label={`Step ${step.num}: ${step.label} ${isCompleted ? "(Completed)" : isActive ? "(Active)" : ""}`}
                  >
                    <div className="stepper-circle">
                      {isCompleted ? <CheckIcon /> : step.num}
                    </div>
                    <span>{step.label}</span>
                  </div>
                  {idx < STEPS.length - 1 && <div className="stepper-line-divider" aria-hidden="true"></div>}
                </React.Fragment>
              );
            })}
          </nav>

          {/* TAB 1: DOCUMENT INGESTION */}
          <div
            role="tabpanel"
            id="panel-document"
            aria-labelledby="tab-document"
            hidden={activeTab !== "document"}
          >
            {activeTab === "document" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "24px" }}>
                  <h1 className="page-title">Document Management</h1>
                  <p className="caption-text">
                    Upload contract files or paste raw text to initiate automated clause extraction, liability analysis, and RAG indexing.
                  </p>
                </header>

                {docError && <div className="alert-banner error" role="alert">⚠️ {docError}</div>}
                {currentDoc && (
                  <div className="alert-banner success" role="status">
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

                      <label htmlFor="file-input-field" className="sr-only">Choose PDF, DOCX, or TXT document file</label>

                      <div
                        className={`dropzone-container ${isDragActive ? "drag-active" : ""}`}
                        onClick={() => document.getElementById("file-input-field").click()}
                        onKeyDown={(e) => e.key === "Enter" && document.getElementById("file-input-field").click()}
                        tabIndex={0}
                        role="button"
                        aria-label="Click or press enter to upload contract file"
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
                        <div className="file-tag-group" aria-label="Supported file formats">
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
                      aria-busy={docLoading}
                    >
                      {docLoading ? <span className="micro-spinner" role="status" aria-label="Parsing file..."></span> : "Upload & Parse Document"}
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

                      <label htmlFor="raw-text-input" className="sr-only">Raw contract text</label>
                      <textarea
                        id="raw-text-input"
                        className="input-textarea"
                        placeholder="Paste contract provisions, clauses, or agreement text..."
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        aria-label="Raw contract text input"
                      ></textarea>
                    </div>

                    <button
                      type="submit"
                      className="btn-cta btn-cta-primary"
                      style={{ width: "100%", marginTop: "24px" }}
                      disabled={docLoading || !textInput.trim()}
                      aria-busy={docLoading}
                    >
                      {docLoading ? <span className="micro-spinner" role="status" aria-label="Processing text..."></span> : "Process Contract Text"}
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>

          {/* TAB 2: RISK AUDIT */}
          <div
            role="tabpanel"
            id="panel-analysis"
            aria-labelledby="tab-analysis"
            hidden={activeTab !== "analysis"}
          >
            {activeTab === "analysis" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <h1 className="page-title">Risk & Clause Audit</h1>
                    <p className="caption-text">AI analysis of financial liabilities, termination triggers, obligations, and risk scores.</p>
                  </div>
                  <button
                    className="btn-cta btn-cta-primary"
                    onClick={handleAnalyze}
                    disabled={analysisLoading || !currentDoc}
                    aria-busy={analysisLoading}
                  >
                    {analysisLoading ? <span className="micro-spinner" role="status" aria-label="Auditing risks..."></span> : "Run Risk Audit"}
                  </button>
                </header>

                {analysisError && <div className="alert-banner error" role="alert">⚠️ {analysisError}</div>}

                {!analysisResult && !analysisLoading && (
                  <div className="empty-placeholder">
                    <ShieldAlertIcon className="empty-placeholder-icon" />
                    <h3>No Risk Audit Generated Yet</h3>
                    <p className="caption-text">Click "Run Risk Audit" above to analyze obligations, key dates, and clause scores.</p>
                  </div>
                )}

                {analysisResult && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    <div className="panel-box">
                      <h2 className="section-header">Executive Summary</h2>
                      <p style={{ color: "var(--text-primary)", fontSize: "15px", lineHeight: "1.6" }}>
                        {analysisResult.summary}
                      </p>
                    </div>

                    <div className="dual-panel-grid">
                      <div className="panel-box">
                        <h2 className="section-header" style={{ color: "var(--color-warning)" }}>Key Risks</h2>
                        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "8px", marginTop: "12px" }}>
                          {analysisResult.risks?.map((r, i) => (
                            <li key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                              <span style={{ color: "var(--color-warning)" }}>⚠️</span> {r}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="panel-box">
                        <h2 className="section-header" style={{ color: "var(--color-success)" }}>Key Obligations</h2>
                        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "8px", marginTop: "12px" }}>
                          {analysisResult.obligations?.map((o, i) => (
                            <li key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                              <span style={{ color: "var(--color-success)" }}>✓</span> {o}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {analysisResult.risk_clauses?.length > 0 && (
                      <div className="panel-box">
                        <h2 className="section-header">Risk Score Breakdown</h2>
                        <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
                          {analysisResult.risk_clauses.map((clause, idx) => (
                            <div key={idx} style={{ padding: "12px", background: "var(--bg-card-elevated)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-divider)" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                                <strong>{clause.title}</strong>
                                <span style={{ fontWeight: "700", color: clause.score > 70 ? "var(--color-danger)" : "var(--color-warning)" }}>
                                  Risk Score: {clause.score}/100
                                </span>
                              </div>
                              <p className="caption-text">{clause.reason}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* TAB 3: COMPARE */}
          <div
            role="tabpanel"
            id="panel-compare"
            aria-labelledby="tab-compare"
            hidden={activeTab !== "compare"}
          >
            {activeTab === "compare" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "24px" }}>
                  <h1 className="page-title">Contract Comparison</h1>
                  <p className="caption-text">Compare two versions of a contract or compare a notice against a counter-response.</p>
                </header>

                {compareError && <div className="alert-banner error" role="alert">⚠️ {compareError}</div>}

                <form onSubmit={handleCompare} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                  <div className="dual-panel-grid">
                    <div className="panel-box">
                      <label htmlFor="doc-a-id" className="section-header">Document A (ID or Text)</label>
                      <input
                        id="doc-a-id"
                        type="text"
                        className="input-textarea"
                        style={{ height: "40px", marginBottom: "8px" }}
                        placeholder="Doc ID A (e.g. current loaded doc)"
                        value={docA.docId}
                        onChange={(e) => setDocA({ ...docA, docId: e.target.value })}
                      />
                      <label htmlFor="doc-a-text" className="sr-only">Document A raw text</label>
                      <textarea
                        id="doc-a-text"
                        className="input-textarea"
                        placeholder="Or paste Document A text here..."
                        value={docA.text}
                        onChange={(e) => setDocA({ ...docA, text: e.target.value })}
                      ></textarea>
                    </div>

                    <div className="panel-box">
                      <label htmlFor="doc-b-id" className="section-header">Document B (ID or Text)</label>
                      <input
                        id="doc-b-id"
                        type="text"
                        className="input-textarea"
                        style={{ height: "40px", marginBottom: "8px" }}
                        placeholder="Doc ID B"
                        value={docB.docId}
                        onChange={(e) => setDocB({ ...docB, docId: e.target.value })}
                      />
                      <label htmlFor="doc-b-text" className="sr-only">Document B raw text</label>
                      <textarea
                        id="doc-b-text"
                        className="input-textarea"
                        placeholder="Or paste Document B text here..."
                        value={docB.text}
                        onChange={(e) => setDocB({ ...docB, text: e.target.value })}
                      ></textarea>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <label htmlFor="user-role-select" style={{ fontWeight: "600" }}>Representing Role:</label>
                    <select
                      id="user-role-select"
                      className="btn-secondary"
                      style={{ padding: "8px 12px" }}
                      value={userRole}
                      onChange={(e) => setUserRole(e.target.value)}
                    >
                      <option value="Buyer">Buyer / Licensee</option>
                      <option value="Seller">Seller / Licensor</option>
                      <option value="Neutral">Neutral Auditor</option>
                    </select>

                    <button
                      type="submit"
                      className="btn-cta btn-cta-primary"
                      disabled={compareLoading}
                      aria-busy={compareLoading}
                    >
                      {compareLoading ? <span className="micro-spinner" role="status" aria-label="Comparing..."></span> : "Compare Contracts"}
                    </button>
                  </div>
                </form>

                {compareResult && (
                  <div style={{ marginTop: "24px" }} className="panel-box">
                    <h2 className="section-header">Comparison Analysis</h2>
                    <p style={{ marginTop: "8px", fontSize: "15px" }}>{compareResult.summary}</p>

                    <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                      {compareResult.differences?.map((diff, idx) => (
                        <div key={idx} style={{ padding: "12px", background: "var(--bg-card-elevated)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-divider)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                            <strong>{diff.clause}</strong>
                            <span style={{ textTransform: "uppercase", fontSize: "12px", fontWeight: "700", color: "var(--accent-primary)" }}>
                              Favors: {diff.favors}
                            </span>
                          </div>
                          <p style={{ fontSize: "13px" }}><strong>Doc A:</strong> {diff.in_a}</p>
                          <p style={{ fontSize: "13px" }}><strong>Doc B:</strong> {diff.in_b}</p>
                          <p className="caption-text" style={{ marginTop: "6px" }}>{diff.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* TAB 4: CHECKLIST */}
          <div
            role="tabpanel"
            id="panel-checklist"
            aria-labelledby="tab-checklist"
            hidden={activeTab !== "checklist"}
          >
            {activeTab === "checklist" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <h1 className="page-title">Compliance & Action Checklist</h1>
                    <p className="caption-text">Action items for your team and structured questions for legal counsel.</p>
                  </div>
                  <button
                    className="btn-cta btn-cta-primary"
                    onClick={handleGenerateChecklist}
                    disabled={checklistLoading || !currentDoc}
                    aria-busy={checklistLoading}
                  >
                    {checklistLoading ? <span className="micro-spinner" role="status" aria-label="Generating..."></span> : "Generate Checklist"}
                  </button>
                </header>

                {checklistError && <div className="alert-banner error" role="alert">⚠️ {checklistError}</div>}

                {!checklistResult && !checklistLoading && (
                  <div className="empty-placeholder">
                    <CheckSquareIcon className="empty-placeholder-icon" />
                    <h3>No Checklist Generated</h3>
                    <p className="caption-text">Click "Generate Checklist" to extract action items and lawyer questions.</p>
                  </div>
                )}

                {checklistResult && (
                  <div className="dual-panel-grid">
                    <div className="panel-box">
                      <h2 className="section-header">Action Items</h2>
                      <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "10px", marginTop: "12px" }}>
                        {checklistResult.checklist?.map((item, idx) => (
                          <li key={idx} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <input type="checkbox" id={`chk-${idx}`} style={{ width: "18px", height: "18px", cursor: "pointer" }} />
                            <label htmlFor={`chk-${idx}`} style={{ cursor: "pointer" }}>{item.item}</label>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="panel-box">
                      <h2 className="section-header">Questions for Lawyer</h2>
                      <ol style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "12px", marginTop: "12px" }}>
                        {checklistResult.lawyer_questions?.map((q, idx) => (
                          <li key={idx}>
                            <strong>{q.question}</strong>
                            <p className="caption-text">{q.context}</p>
                          </li>
                        ))}
                      </ol>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* TAB 5: NEGOTIATION */}
          <div
            role="tabpanel"
            id="panel-negotiation"
            aria-labelledby="tab-negotiation"
            hidden={activeTab !== "negotiation"}
          >
            {activeTab === "negotiation" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "24px" }}>
                  <h1 className="page-title">Negotiation Playbook</h1>
                  <p className="caption-text">Draft counter-clauses and generate tactical negotiation talking points.</p>
                </header>

                {negotiationError && <div className="alert-banner error" role="alert">⚠️ {negotiationError}</div>}

                <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
                  <label htmlFor="clause-topic-input" className="sr-only">Target Clause Topic</label>
                  <input
                    id="clause-topic-input"
                    type="text"
                    className="input-textarea"
                    style={{ height: "42px" }}
                    placeholder="Enter target clause topic (e.g. Liquidated Damages, Termination Fee)..."
                    value={selectedClause}
                    onChange={(e) => setSelectedClause(e.target.value)}
                  />
                  <button
                    className="btn-cta btn-cta-primary"
                    onClick={handleGenerateNegotiation}
                    disabled={negotiationLoading || !currentDoc}
                    aria-busy={negotiationLoading}
                  >
                    {negotiationLoading ? <span className="micro-spinner" role="status" aria-label="Drafting..."></span> : "Generate Strategy"}
                  </button>
                </div>

                {negotiationResult && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    <div className="panel-box">
                      <h2 className="section-header">Suggested Counter-Clause</h2>
                      <pre style={{ whiteSpace: "pre-wrap", background: "var(--bg-app)", padding: "12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-divider)", fontFamily: "var(--font-mono)", fontSize: "13px", marginTop: "8px" }}>
                        {negotiationResult.counter_clause}
                      </pre>
                    </div>

                    <div className="panel-box">
                      <h2 className="section-header">Negotiation Talking Points</h2>
                      <ul style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                        {negotiationResult.talking_points?.map((tp, idx) => (
                          <li key={idx}>{tp}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* TAB 6: CHAT */}
          <div
            role="tabpanel"
            id="panel-chat"
            aria-labelledby="tab-chat"
            hidden={activeTab !== "chat"}
          >
            {activeTab === "chat" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "20px" }}>
                  <h1 className="page-title">AI Legal Assistant</h1>
                  <p className="caption-text">Ask specific questions about the active contract document (RAG Q&A with citations).</p>
                </header>

                {chatError && <div className="alert-banner error" role="alert">⚠️ {chatError}</div>}

                <div style={{ display: "flex", flexDirection: "column", height: "400px", border: "1px solid var(--border-divider)", borderRadius: "var(--radius-md)", overflow: "hidden", background: "var(--bg-card)" }}>
                  <div style={{ flex: 1, padding: "16px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px" }} role="log" aria-label="Chat Message History">
                    {chatMessages.length === 0 && (
                      <p className="caption-text" style={{ textAlign: "center", marginTop: "40px" }}>
                        Ask a question about your contract (e.g. "What is the cure period deadline?")
                      </p>
                    )}
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        style={{
                          alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                          maxWidth: "80%",
                          padding: "10px 14px",
                          borderRadius: "var(--radius-sm)",
                          background: msg.role === "user" ? "var(--accent-primary)" : "var(--bg-card-elevated)",
                          color: "#FFFFFF",
                          border: msg.role === "assistant" ? "1px solid var(--border-divider)" : "none",
                        }}
                      >
                        <div>{msg.text}</div>
                        {msg.confidence !== undefined && (
                          <div style={{ fontSize: "11px", opacity: 0.8, marginTop: "4px" }}>
                            Confidence Score: {(msg.confidence * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  <form onSubmit={handleSendChat} style={{ display: "flex", padding: "12px", borderTop: "1px solid var(--border-divider)", gap: "8px" }}>
                    <label htmlFor="chat-question-input" className="sr-only">Ask a question about the contract</label>
                    <input
                      id="chat-question-input"
                      type="text"
                      className="input-textarea"
                      style={{ height: "42px", flex: 1 }}
                      placeholder="Ask a question about the active contract..."
                      value={chatQuestion}
                      onChange={(e) => setChatQuestion(e.target.value)}
                    />
                    <button
                      type="submit"
                      className="btn-cta btn-cta-primary"
                      disabled={chatLoading || !currentDoc}
                      aria-busy={chatLoading}
                    >
                      {chatLoading ? <span className="micro-spinner" role="status" aria-label="Sending..."></span> : "Send"}
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>

          {/* TAB 7: EXPORT */}
          <div
            role="tabpanel"
            id="panel-export"
            aria-labelledby="tab-export"
            hidden={activeTab !== "export"}
          >
            {activeTab === "export" && (
              <div className="dashboard-card">
                <header style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <h1 className="page-title">Lawyer Pack Export</h1>
                    <p className="caption-text">Generate and download a comprehensive executive briefing document for legal counsel.</p>
                  </div>
                  <button
                    className="btn-cta btn-cta-primary"
                    onClick={handleExportLawyerPack}
                    disabled={exportLoading || !currentDoc}
                    aria-busy={exportLoading}
                  >
                    {exportLoading ? <span className="micro-spinner" role="status" aria-label="Building pack..."></span> : "Generate Lawyer Pack"}
                  </button>
                </header>

                {exportError && <div className="alert-banner error" role="alert">⚠️ {exportError}</div>}
                {copiedToast && <div className="alert-banner success" role="status">✅ Copied to clipboard!</div>}

                {exportContent ? (
                  <div className="panel-box">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                      <h2 className="section-header">Export Preview</h2>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button className="btn-secondary" onClick={copyExport}>Copy Text</button>
                        <button className="btn-cta btn-cta-primary" onClick={downloadExport}>Download TXT</button>
                      </div>
                    </div>
                    <pre style={{ whiteSpace: "pre-wrap", background: "var(--bg-app)", padding: "16px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-divider)", fontFamily: "var(--font-mono)", fontSize: "13px", maxHeight: "500px", overflowY: "auto" }}>
                      {exportContent}
                    </pre>
                  </div>
                ) : (
                  <div className="empty-placeholder">
                    <DownloadIcon className="empty-placeholder-icon" />
                    <h3>No Lawyer Pack Generated</h3>
                    <p className="caption-text">Click "Generate Lawyer Pack" to compile all audit findings, checklist, and negotiation notes.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>

      <footer role="contentinfo" style={{ textAlign: "center", padding: "16px", borderTop: "1px solid var(--border-divider)", color: "var(--text-secondary)", fontSize: "12px" }}>
        LegiFlow Legal AI Platform • General legal information, not formal legal advice.
      </footer>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
