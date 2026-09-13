import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const api = import.meta.env.VITE_API_URL || "";

function App() {
  const [health, setHealth] = useState("Checking backend…");

  useEffect(() => {
    fetch(`${api}/health`)
      .then((response) => response.json())
      .then(({ status }) => setHealth(`Backend: ${status}`))
      .catch(() => setHealth("Backend unavailable"));
  }, []);

  return <main><h1>LegiFlow</h1><p>General legal information, not legal advice.</p><p>{health}</p></main>;
}

createRoot(document.getElementById("root")).render(<App />);
