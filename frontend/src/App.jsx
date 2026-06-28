import { useState, useEffect } from "react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const COLORS = {
  bg: "#0A0E1A",
  card: "#111827",
  cardBorder: "#1F2937",
  accent: "#6366F1",
  accentLight: "#818CF8",
  accentGlow: "rgba(99,102,241,0.15)",
  green: "#10B981",
  yellow: "#F59E0B",
  red: "#EF4444",
  text: "#F9FAFB",
  textMuted: "#9CA3AF",
  textDim: "#6B7280",
};

const categoryColor = (cat) => ({
  Government: "#3B82F6",
  Private: "#8B5CF6",
  Merit: "#F59E0B",
  "Need-based": "#10B981",
  Research: "#EC4899",
  Sports: "#F97316",
  Minority: "#14B8A6",
}[cat] || COLORS.accent);

function ScoreRing({ score }) {
  const color = score >= 80 ? COLORS.green : score >= 60 ? COLORS.yellow : COLORS.red;
  return (
    <div style={{ position: "relative", width: 56, height: 56 }}>
      <svg width="56" height="56" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="28" cy="28" r="22" fill="none" stroke="#1F2937" strokeWidth="4" />
        <circle cx="28" cy="28" r="22" fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={`${(score / 100) * 138.2} 138.2`} strokeLinecap="round" />
      </svg>
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        transform: "translate(-50%,-50%)",
        fontSize: 12, fontWeight: 700, color,
      }}>{score}%</div>
    </div>
  );
}

function ScholarshipCard({ s, index }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div onClick={() => setExpanded(!expanded)} style={{
      background: COLORS.card,
      border: `1px solid ${expanded ? COLORS.accentLight : COLORS.cardBorder}`,
      borderLeft: `3px solid ${categoryColor(s.category)}`,
      borderRadius: 16, padding: "20px 24px",
      cursor: "pointer", transition: "all 0.2s", marginBottom: 12,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{
              background: categoryColor(s.category) + "22", color: categoryColor(s.category),
              fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 20,
            }}>{s.category}</span>
            <span style={{ color: COLORS.textDim, fontSize: 12 }}>#{index + 1}</span>
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.text, marginBottom: 4 }}>{s.name}</div>
          <div style={{ fontSize: 13, color: COLORS.textMuted }}>{s.provider}</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
          <ScoreRing score={s.match_score} />
          <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.green }}>{s.amount}</div>
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${COLORS.cardBorder}` }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Eligibility</div>
              <div style={{ fontSize: 13, color: COLORS.text }}>{s.eligibility}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Deadline</div>
              <div style={{ fontSize: 13, color: COLORS.yellow, fontWeight: 600 }}>{s.deadline}</div>
            </div>
          </div>
          <div style={{
            background: COLORS.accentGlow, borderRadius: 10,
            padding: "10px 14px", fontSize: 13, color: COLORS.accentLight, marginBottom: 14,
          }}>💡 {s.match_reason}</div>
          <a href={s.apply_link} target="_blank" rel="noreferrer"
            onClick={e => e.stopPropagation()}
            style={{
              display: "inline-block", background: COLORS.accent, color: "#fff",
              padding: "8px 20px", borderRadius: 8,
              fontSize: 13, fontWeight: 600, textDecoration: "none",
            }}>Apply Now →</a>
        </div>
      )}
    </div>
  );
}

function ProfileForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    name: "", course: "", year: "", percentage: "",
    income: "", category: "", state: "", interests: "",
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const inputStyle = {
    width: "100%", background: "#1F2937", border: "1px solid #374151",
    borderRadius: 10, padding: "10px 14px", color: COLORS.text,
    fontSize: 14, outline: "none", boxSizing: "border-box", fontFamily: "inherit",
  };
  const labelStyle = {
    fontSize: 12, color: COLORS.textMuted, marginBottom: 6,
    display: "block", fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.8,
  };

  return (
    <div style={{
      background: COLORS.card, border: `1px solid ${COLORS.cardBorder}`,
      borderRadius: 20, padding: 28,
    }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, marginBottom: 6 }}>Your Profile</div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginBottom: 22 }}>Fill once. AI finds your best matches instantly.</div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {[
          { key: "name", label: "Full Name", placeholder: "Rahul Sharma" },
          { key: "course", label: "Course / Stream", placeholder: "B.Tech Computer Science" },
        ].map(f => (
          <div key={f.key}>
            <label style={labelStyle}>{f.label}</label>
            <input style={inputStyle} placeholder={f.placeholder}
              value={form[f.key]} onChange={e => set(f.key, e.target.value)} />
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginTop: 16 }}>
        {[
          { key: "year", label: "Year", placeholder: "2nd Year" },
          { key: "percentage", label: "Marks / CGPA", placeholder: "85% or 8.5 CGPA" },
          { key: "income", label: "Family Income", placeholder: "₹3 LPA" },
        ].map(f => (
          <div key={f.key}>
            <label style={labelStyle}>{f.label}</label>
            <input style={inputStyle} placeholder={f.placeholder}
              value={form[f.key]} onChange={e => set(f.key, e.target.value)} />
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <div>
          <label style={labelStyle}>Category</label>
          <select style={inputStyle} value={form.category} onChange={e => set("category", e.target.value)}>
            <option value="">Select category</option>
            {["General", "OBC", "SC", "ST", "EWS", "Minority"].map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>State</label>
          <input style={inputStyle} placeholder="Maharashtra"
            value={form.state} onChange={e => set("state", e.target.value)} />
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <label style={labelStyle}>Achievements / Special Background</label>
        <textarea style={{ ...inputStyle, minHeight: 70, resize: "vertical" }}
          placeholder="Sports captain, NSS volunteer, published research, disability, etc."
          value={form.interests} onChange={e => set("interests", e.target.value)} />
      </div>

      <button onClick={() => onSubmit(form)}
        disabled={loading || !form.name || !form.course}
        style={{
          marginTop: 20, width: "100%",
          background: loading ? "#374151" : `linear-gradient(135deg, ${COLORS.accent}, #8B5CF6)`,
          color: "#fff", border: "none", borderRadius: 12,
          padding: "14px 0", fontSize: 15, fontWeight: 700,
          cursor: loading ? "not-allowed" : "pointer", transition: "all 0.2s",
        }}>
        {loading ? "🔍 Finding Scholarships..." : "✨ Find My Scholarships"}
      </button>
    </div>
  );
}

export default function App() {
  const [step, setStep] = useState("form");
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [studentName, setStudentName] = useState("");
  const [dots, setDots] = useState(0);

  useEffect(() => {
    if (step !== "loading") return;
    const t = setInterval(() => setDots(d => (d + 1) % 4), 500);
    return () => clearInterval(t);
  }, [step]);

  const handleSubmit = async (form) => {
    setStudentName(form.name.split(" ")[0]);
    setStep("loading");
    setError("");
    try {
      const res = await fetch(`${API_BASE}/find-scholarships`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("API error");
      const data = await res.json();
      setResults(data);
      setStep("results");
    } catch (e) {
      setError("Something went wrong. Make sure backend is running. See README.md");
      setStep("form");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, fontFamily: "'Inter', -apple-system, sans-serif", color: COLORS.text }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${COLORS.cardBorder}`, padding: "16px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "rgba(10,14,26,0.95)", backdropFilter: "blur(10px)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: `linear-gradient(135deg, ${COLORS.accent}, #8B5CF6)`,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
          }}>🎓</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: -0.5 }}>ScholarAI</div>
            <div style={{ fontSize: 11, color: COLORS.textMuted }}>Find scholarships in 30 seconds</div>
          </div>
        </div>
        {step === "results" && (
          <button onClick={() => { setStep("form"); setResults(null); }}
            style={{
              background: "transparent", border: `1px solid ${COLORS.cardBorder}`,
              color: COLORS.textMuted, padding: "6px 16px", borderRadius: 8, cursor: "pointer", fontSize: 13,
            }}>← New Search</button>
        )}
      </div>

      <div style={{ maxWidth: 780, margin: "0 auto", padding: "32px 20px" }}>

        {/* Hero */}
        {step === "form" && (
          <div style={{ textAlign: "center", marginBottom: 36 }}>
            <div style={{
              display: "inline-block", background: COLORS.accentGlow,
              border: `1px solid ${COLORS.accent}44`, color: COLORS.accentLight,
              fontSize: 12, fontWeight: 600, padding: "6px 16px", borderRadius: 20,
              marginBottom: 20, letterSpacing: 1, textTransform: "uppercase",
            }}>AI-Powered • Free • Instant</div>
            <h1 style={{
              fontSize: "clamp(28px,5vw,48px)", fontWeight: 900, lineHeight: 1.15, marginBottom: 16,
              background: `linear-gradient(135deg, ${COLORS.text}, ${COLORS.accentLight})`,
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>Never Miss a<br />Scholarship Again</h1>
            <p style={{ fontSize: 16, color: COLORS.textMuted, maxWidth: 440, margin: "0 auto 20px" }}>
              70% of eligible students miss scholarships. AI matches you to funding in 30 seconds — not 3 hours.
            </p>
            <div style={{ display: "flex", justifyContent: "center", gap: 28, marginBottom: 8 }}>
              {[["₹50Cr+", "Funding Found"], ["20,000+", "Students Helped"], ["200+", "Scholarships"]].map(([n, l]) => (
                <div key={l} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: COLORS.accentLight }}>{n}</div>
                  <div style={{ fontSize: 11, color: COLORS.textDim }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading */}
        {step === "loading" && (
          <div style={{ textAlign: "center", padding: "80px 20px" }}>
            <div style={{
              width: 80, height: 80, borderRadius: "50%",
              background: COLORS.accentGlow, border: `2px solid ${COLORS.accent}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 36, margin: "0 auto 24px",
            }}>🔍</div>
            <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 10 }}>
              Finding your matches{".".repeat(dots)}
            </div>
            <div style={{ color: COLORS.textMuted, fontSize: 14 }}>Scanning 200+ scholarships for {studentName}</div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            background: "#EF444420", border: "1px solid #EF4444",
            borderRadius: 12, padding: 16, marginBottom: 20, color: "#FCA5A5", fontSize: 14,
          }}>{error}</div>
        )}

        {step === "form" && <ProfileForm onSubmit={handleSubmit} loading={false} />}

        {/* Results */}
        {step === "results" && results && (
          <div>
            <div style={{
              background: `linear-gradient(135deg, ${COLORS.accentGlow}, #8B5CF620)`,
              border: `1px solid ${COLORS.accent}44`, borderRadius: 20, padding: 24, marginBottom: 28,
            }}>
              <div style={{ fontSize: 13, color: COLORS.accentLight, fontWeight: 600, marginBottom: 8 }}>
                🎉 Hey {studentName}, here's what we found
              </div>
              <div style={{ fontSize: 15, color: COLORS.text, marginBottom: 16, lineHeight: 1.6 }}>{results.summary}</div>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontSize: 26, fontWeight: 900, color: COLORS.green }}>{results.total_funding}</div>
                  <div style={{ fontSize: 12, color: COLORS.textMuted }}>Total potential funding</div>
                </div>
                <div>
                  <div style={{ fontSize: 26, fontWeight: 900, color: COLORS.accentLight }}>{results.matches?.length}</div>
                  <div style={{ fontSize: 12, color: COLORS.textMuted }}>Scholarships matched</div>
                </div>
              </div>
            </div>

            {results.tips?.length > 0 && (
              <div style={{
                background: COLORS.card, border: `1px solid ${COLORS.cardBorder}`,
                borderRadius: 16, padding: 20, marginBottom: 24,
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: COLORS.yellow }}>💡 Pro Tips For You</div>
                {results.tips.map((t, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8, fontSize: 13, color: COLORS.textMuted }}>
                    <span style={{ color: COLORS.accent, fontWeight: 700 }}>→</span> {t}
                  </div>
                ))}
              </div>
            )}

            <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.textDim, marginBottom: 14, textTransform: "uppercase", letterSpacing: 1 }}>
              Your Matches — tap to expand
            </div>
            {results.matches?.map((s, i) => <ScholarshipCard key={i} s={s} index={i} />)}

            <div style={{
              marginTop: 32, background: COLORS.card, border: `1px solid ${COLORS.cardBorder}`,
              borderRadius: 20, padding: 24, textAlign: "center",
            }}>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>Share Your Results 🚀</div>
              <div style={{ fontSize: 13, color: COLORS.textMuted, marginBottom: 16 }}>
                Found {results.total_funding} in scholarships in 30 seconds? Post it on LinkedIn and get noticed!
              </div>
              <button onClick={() => {
                const text = `I found ${results.total_funding} in scholarships in 30 seconds using AI!\n\nScholarAI matched me to ${results.matches?.length} scholarships instantly.\n\n#ScholarAI #Scholarships #IndianStudents`;
                window.open(`https://www.linkedin.com/sharing/share-offsite/?summary=${encodeURIComponent(text)}`);
              }} style={{
                background: "#0077B5", color: "#fff", border: "none",
                borderRadius: 10, padding: "10px 24px", fontSize: 14, fontWeight: 600, cursor: "pointer",
              }}>Share on LinkedIn</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
