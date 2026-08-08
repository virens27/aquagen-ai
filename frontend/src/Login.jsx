import { useState } from "react";
import { supabase } from "./supabaseClient";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("signin"); // "signin" or "signup"
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    if (mode === "signin") {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) setError(error.message);
    } else {
      const { error } = await supabase.auth.signUp({
        email,
        password,
      });
      if (error) {
        setError(error.message);
      } else {
        setMessage(
          "Check your email to confirm your account before signing in.",
        );
      }
    }
    setLoading(false);
  };

  const handleGoogleSignIn = async () => {
    setError("");
    await supabase.auth.signInWithOAuth({
      provider: "google",
    });
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#F0F4F8",
        fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      <div
        style={{
          background: "white",
          borderRadius: "14px",
          boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
          padding: "40px",
          width: "100%",
          maxWidth: "380px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              background: "linear-gradient(135deg, #2E86AB, #4C9A6F)",
              borderRadius: "12px",
              margin: "0 auto 14px",
            }}
          />
          <div
            style={{
              fontWeight: "700",
              fontSize: "1.3rem",
              color: "#1B3B5F",
            }}
          >
            AquaGen AI
          </div>
          <div style={{ fontSize: "0.85rem", color: "#888", marginTop: "4px" }}>
            {mode === "signin" ? "Sign in to continue" : "Create your account"}
          </div>
        </div>

        <form onSubmit={handleEmailAuth}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            required
            style={{
              width: "100%",
              padding: "10px 14px",
              borderRadius: "9px",
              border: "1.5px solid #E0EEF5",
              fontSize: "0.92rem",
              outline: "none",
              marginBottom: "10px",
              boxSizing: "border-box",
            }}
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
            minLength={6}
            style={{
              width: "100%",
              padding: "10px 14px",
              borderRadius: "9px",
              border: "1.5px solid #E0EEF5",
              fontSize: "0.92rem",
              outline: "none",
              marginBottom: "14px",
              boxSizing: "border-box",
            }}
          />

          {error && (
            <div
              style={{
                color: "#C0392B",
                fontSize: "0.82rem",
                marginBottom: "10px",
              }}
            >
              {error}
            </div>
          )}
          {message && (
            <div
              style={{
                color: "#4C9A6F",
                fontSize: "0.82rem",
                marginBottom: "10px",
              }}
            >
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "11px",
              background: loading
                ? "#ccc"
                : "linear-gradient(135deg, #2E86AB, #1B6B8A)",
              color: "white",
              border: "none",
              borderRadius: "9px",
              fontSize: "0.92rem",
              fontWeight: "600",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {mode === "signin" ? "Sign In" : "Sign Up"}
          </button>
        </form>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            margin: "18px 0",
          }}
        >
          <div style={{ flex: 1, height: "1px", background: "#E0EEF5" }} />
          <div style={{ fontSize: "0.78rem", color: "#999" }}>or</div>
          <div style={{ flex: 1, height: "1px", background: "#E0EEF5" }} />
        </div>

        <button
          onClick={handleGoogleSignIn}
          style={{
            width: "100%",
            padding: "10px",
            background: "white",
            color: "#1B3B5F",
            border: "1.5px solid #E0EEF5",
            borderRadius: "9px",
            fontSize: "0.9rem",
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          Continue with Google
        </button>

        <div
          style={{
            textAlign: "center",
            marginTop: "20px",
            fontSize: "0.82rem",
            color: "#888",
          }}
        >
          {mode === "signin" ? (
            <>
              Don't have an account?{" "}
              <span
                onClick={() => {
                  setMode("signup");
                  setError("");
                  setMessage("");
                }}
                style={{
                  color: "#2E86AB",
                  cursor: "pointer",
                  fontWeight: "600",
                }}
              >
                Sign up
              </span>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <span
                onClick={() => {
                  setMode("signin");
                  setError("");
                  setMessage("");
                }}
                style={{
                  color: "#2E86AB",
                  cursor: "pointer",
                  fontWeight: "600",
                }}
              >
                Sign in
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}