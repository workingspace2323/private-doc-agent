import { useEffect, useState } from "react";

export default function App() {
  const [files, setFiles] = useState([]);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]);

  const API = "http://127.0.0.1:8000";

  // ---------------- LOAD FILES ----------------
  const loadFiles = async () => {
    const res = await fetch(`${API}/api/files`);
    const data = await res.json();
    setFiles(data.files || []);
  };

  useEffect(() => {
    loadFiles();
  }, []);

  // ---------------- ASK ----------------
  const ask = async () => {
    if (!question) return;

    const form = new FormData();
    form.append("question", question);
    form.append("filename", files[0] || "");

    const res = await fetch(`${API}/api/query`, {
      method: "POST",
      body: form,
    });

    const data = await res.json();

    setChat((prev) => [
      ...prev,
      { role: "user", text: question },
      { role: "bot", text: data.answer },
    ]);

    setQuestion("");
  };

  // ---------------- DELETE FILE (FIXED) ----------------
  const deleteFile = async (filename) => {
    const res = await fetch(
      `${API}/api/delete?filename=${encodeURIComponent(filename)}`,
      {
        method: "DELETE", // 🔥 IMPORTANT
      }
    );

    const data = await res.json();
    console.log("DELETE RESPONSE:", data);

    loadFiles();
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h2>📄 AI Document Agent</h2>

      {/* INPUT */}
      <div style={{ marginBottom: 20 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something..."
          style={{ padding: 10, width: "60%" }}
        />
        <button onClick={ask} style={{ padding: 10, marginLeft: 10 }}>
          Ask
        </button>
      </div>

      {/* CHAT */}
      <div style={{ marginBottom: 30 }}>
        {chat.map((c, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <b>{c.role}:</b> {c.text}
          </div>
        ))}
      </div>

      {/* FILES */}
      <h3>📁 Files</h3>

      <ul>
        {files.map((f, i) => (
          <li key={i} style={{ marginBottom: 8 }}>
            {f}

            <button
              onClick={() => deleteFile(f)}
              style={{
                marginLeft: 10,
                background: "red",
                color: "white",
                border: "none",
                padding: "5px 10px",
                cursor: "pointer",
              }}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}