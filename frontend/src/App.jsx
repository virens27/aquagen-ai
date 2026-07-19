import { useState } from "react";
import axios from "axios";
import MapView from "./MapView";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

// Inline SVG Icons — no emoji, no icon library needed
const Icons = {
  database: (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#2E86AB"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  ),
  globe: (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#2E86AB"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  ),
  wave: (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#2E86AB"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
      <path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
      <path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
    </svg>
  ),
  send: (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  bot: (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="15" x2="8" y2="15" />
      <line x1="16" y1="15" x2="16" y2="15" />
    </svg>
  ),
  user: (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  history: (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#2E86AB"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="1 4 1 10 7 10" />
      <path d="M3.51 15a9 9 0 1 0 .49-3.51" />
    </svg>
  ),
  sparkle: (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#4C9A6F"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
};

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    if (!question.trim()) return;
    const userMessage = { role: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/ask`, {
        question,
      });
      const { explanation, data, sql } = response.data;
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: explanation, data, sql },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Something went wrong. Please try again." },
      ]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") askQuestion();
  };

  const renderChart = (data) => {
    if (!data || data.length <= 1) return null;
    const allKeys = Object.keys(data[0]);
    const xKey =
      allKeys.find((k) =>
        ["lat", "lon", "date", "depth", "month"].includes(k),
      ) || allKeys[0];
    const yKeys = allKeys.filter((k) => k !== xKey);
    return (
      <div style={{ marginTop: "12px" }}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 10 }}
              label={{
                value: xKey,
                position: "insideBottom",
                offset: -2,
                fontSize: 11,
              }}
            />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{ borderRadius: "8px", fontSize: "0.85rem" }}
            />
            <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
            {yKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={i === 0 ? "#2E86AB" : "#4C9A6F"}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const suggestedQuestions = [
    "What is the average temperature in the Indian Ocean?",
    "Show me ocean temperature at 50 different locations on a map",
    "What is the average salinity by depth?",
    "What is the single highest temperature value in the dataset?",
    "Show me average temperature by month",
  ];

  const stats = [
    { icon: Icons.database, value: "228,060", label: "Ocean Records" },
    { icon: Icons.globe, value: "Indian Ocean", label: "Region Covered" },
    { icon: Icons.wave, value: "ARGO Floats", label: "Data Source" },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#F0F4F8",
        fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "20px 24px",
      }}
    >
      {/* Header */}
      <div
        style={{
          width: "100%",
          maxWidth: "1140px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
          padding: "14px 24px",
          background: "white",
          borderRadius: "14px",
          boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              background: "linear-gradient(135deg, #2E86AB, #4C9A6F)",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {Icons.wave}
          </div>
          <div>
            <div
              style={{
                fontWeight: "700",
                fontSize: "1.15rem",
                color: "#1B3B5F",
                letterSpacing: "-0.01em",
              }}
            >
              AquaGen AI
            </div>
            <div
              style={{ fontSize: "0.72rem", color: "#888", marginTop: "1px" }}
            >
              Ocean Data Intelligence Platform
            </div>
          </div>
        </div>

        {/* Stats inline in header */}
        <div style={{ display: "flex", gap: "32px" }}>
          {stats.map((s) => (
            <div
              key={s.label}
              style={{ display: "flex", alignItems: "center", gap: "10px" }}
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  background: "#EBF5FB",
                  borderRadius: "9px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                {s.icon}
              </div>
              <div>
                <div
                  style={{
                    fontWeight: "600",
                    fontSize: "0.88rem",
                    color: "#1B3B5F",
                  }}
                >
                  {s.value}
                </div>
                <div style={{ fontSize: "0.7rem", color: "#999" }}>
                  {s.label}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Layout */}
      <div
        style={{
          width: "100%",
          maxWidth: "1140px",
          display: "flex",
          gap: "16px",
          alignItems: "flex-start",
        }}
      >
        {/* Sidebar */}
        <div
          style={{
            width: "250px",
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          {/* Chat History Card */}
          <div
            style={{
              background: "white",
              borderRadius: "14px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "0.72rem",
                fontWeight: "700",
                color: "#999",
                textTransform: "uppercase",
                letterSpacing: "0.07em",
                marginBottom: "10px",
              }}
            >
              {Icons.history} Chat History
            </div>

            {messages.filter((m) => m.role === "user").length === 0 ? (
              <div
                style={{
                  color: "#ccc",
                  fontSize: "0.8rem",
                  textAlign: "center",
                  padding: "16px 0",
                }}
              >
                No queries yet
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  maxHeight: "180px",
                  overflowY: "auto",
                }}
              >
                {messages
                  .filter((m) => m.role === "user")
                  .map((m, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "7px 10px",
                        borderRadius: "8px",
                        background: "#F0F7FF",
                        fontSize: "0.78rem",
                        color: "#1B3B5F",
                        borderLeft: "3px solid #2E86AB",
                        lineHeight: "1.3",
                      }}
                    >
                      {m.text.length > 48 ? m.text.slice(0, 48) + "…" : m.text}
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* Suggested Questions Card */}
          <div
            style={{
              background: "white",
              borderRadius: "14px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "0.72rem",
                fontWeight: "700",
                color: "#999",
                textTransform: "uppercase",
                letterSpacing: "0.07em",
                marginBottom: "10px",
              }}
            >
              {Icons.sparkle} Try These
            </div>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => setQuestion(q)}
                  style={{
                    padding: "8px 10px",
                    background: "#F8FBFF",
                    border: "1px solid #D0E8F5",
                    borderRadius: "8px",
                    color: "#2E86AB",
                    fontSize: "0.76rem",
                    cursor: "pointer",
                    textAlign: "left",
                    lineHeight: "1.35",
                    transition: "all 0.15s",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = "#2E86AB";
                    e.currentTarget.style.color = "white";
                    e.currentTarget.style.borderColor = "#2E86AB";
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.background = "#F8FBFF";
                    e.currentTarget.style.color = "#2E86AB";
                    e.currentTarget.style.borderColor = "#D0E8F5";
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          {/* Chat Window */}
          <div
            style={{
              background: "white",
              borderRadius: "14px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
              padding: "20px",
              minHeight: "460px",
              maxHeight: "520px",
              overflowY: "auto",
            }}
          >
            {messages.length === 0 && (
              <div
                style={{
                  textAlign: "center",
                  color: "#bbb",
                  marginTop: "100px",
                }}
              >
                <div
                  style={{
                    width: "52px",
                    height: "52px",
                    background: "linear-gradient(135deg, #2E86AB22, #4C9A6F22)",
                    borderRadius: "14px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 14px",
                  }}
                >
                  {Icons.wave}
                </div>
                <div
                  style={{
                    fontWeight: "600",
                    color: "#999",
                    fontSize: "0.95rem",
                  }}
                >
                  Welcome to AquaGen AI
                </div>
                <div
                  style={{
                    fontSize: "0.82rem",
                    marginTop: "6px",
                    color: "#bbb",
                  }}
                >
                  Select a question from the sidebar or type below
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent:
                    msg.role === "user" ? "flex-end" : "flex-start",
                  marginBottom: "16px",
                  alignItems: "flex-start",
                  gap: "8px",
                }}
              >
                {msg.role === "bot" && (
                  <div
                    style={{
                      width: "30px",
                      height: "30px",
                      borderRadius: "9px",
                      background: "linear-gradient(135deg, #2E86AB, #4C9A6F)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      marginTop: "2px",
                    }}
                  >
                    {Icons.bot}
                  </div>
                )}
                <div
                  style={{
                    maxWidth: "78%",
                    background:
                      msg.role === "user"
                        ? "linear-gradient(135deg, #2E86AB, #1B6B8A)"
                        : "#F5F8FA",
                    color: msg.role === "user" ? "white" : "#1B3B5F",
                    borderRadius:
                      msg.role === "user"
                        ? "14px 14px 4px 14px"
                        : "4px 14px 14px 14px",
                    padding: "11px 15px",
                    fontSize: "0.9rem",
                    lineHeight: "1.55",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                  }}
                >
                  {msg.text}
                  {msg.data && msg.data.length > 1 && (
                    <>
                      {msg.data[0].hasOwnProperty("lat") &&
                      msg.data[0].hasOwnProperty("lon") ? (
                        <MapView data={msg.data} />
                      ) : (
                        renderChart(msg.data)
                      )}
                    </>
                  )}
                  {msg.sql && (
                    <div style={{ marginTop: "8px" }}>
                      <div
                        style={{
                          padding: "6px 10px",
                          background: "rgba(0,0,0,0.05)",
                          borderRadius: "6px",
                          fontSize: "0.72rem",
                          color: "#999",
                          fontFamily: "'Courier New', monospace",
                          marginBottom: "6px",
                        }}
                      >
                        {msg.sql}
                      </div>
                      {msg.data && msg.data.length > 0 && (
                        <button
                          onClick={() => {
                            const headers = Object.keys(msg.data[0]).join(",");
                            const rows = msg.data
                              .map((r) => Object.values(r).join(","))
                              .join("\n");
                            const csv = headers + "\n" + rows;
                            const blob = new Blob([csv], { type: "text/csv" });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = "aquagen_results.csv";
                            a.click();
                            URL.revokeObjectURL(url);
                          }}
                          style={{
                            padding: "5px 12px",
                            background: "#4C9A6F",
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            fontSize: "0.75rem",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "5px",
                          }}
                        >
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="white"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="7 10 12 15 17 10" />
                            <line x1="12" y1="15" x2="12" y2="3" />
                          </svg>
                          Export CSV
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {msg.role === "user" && (
                  <div
                    style={{
                      width: "30px",
                      height: "30px",
                      borderRadius: "9px",
                      background: "#1B3B5F",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      marginTop: "2px",
                    }}
                  >
                    {Icons.user}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div
                style={{ display: "flex", alignItems: "center", gap: "8px" }}
              >
                <div
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "9px",
                    background: "linear-gradient(135deg, #2E86AB, #4C9A6F)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {Icons.bot}
                </div>
                <div
                  style={{
                    background: "#F5F8FA",
                    padding: "11px 16px",
                    borderRadius: "4px 14px 14px 14px",
                    fontSize: "0.88rem",
                    color: "#888",
                    display: "flex",
                    gap: "4px",
                    alignItems: "center",
                  }}
                >
                  <span style={{ animation: "pulse 1s infinite" }}>
                    Analyzing ocean data
                  </span>
                  <span>...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div
            style={{
              display: "flex",
              gap: "10px",
              background: "white",
              borderRadius: "14px",
              padding: "10px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
            }}
          >
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about ocean data..."
              style={{
                flex: 1,
                padding: "10px 14px",
                borderRadius: "9px",
                border: "1.5px solid #E0EEF5",
                fontSize: "0.92rem",
                outline: "none",
                color: "#1B3B5F",
                background: "#F8FBFF",
                transition: "border-color 0.15s",
              }}
              onFocus={(e) => (e.target.style.borderColor = "#2E86AB")}
              onBlur={(e) => (e.target.style.borderColor = "#E0EEF5")}
            />
            <button
              onClick={askQuestion}
              disabled={loading}
              style={{
                padding: "10px 18px",
                background: loading
                  ? "#ccc"
                  : "linear-gradient(135deg, #2E86AB, #1B6B8A)",
                color: "white",
                border: "none",
                borderRadius: "9px",
                fontSize: "0.92rem",
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "7px",
                fontWeight: "600",
                transition: "opacity 0.15s",
              }}
              onMouseOver={(e) => {
                if (!loading) e.currentTarget.style.opacity = "0.9";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.opacity = "1";
              }}
            >
              {Icons.send} Ask
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
