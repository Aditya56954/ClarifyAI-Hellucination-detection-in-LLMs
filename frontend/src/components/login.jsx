import { useState } from "react";
import { ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { loginUser } from "../api/clarifyApi";
import "./Login.css";

function Login({ onLoginSuccess, onSwitchToRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError("Please enter your email.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    try {
      setLoading(true);

      await loginUser(
        email.trim(),
        password
      );

      if (onLoginSuccess) {
        await onLoginSuccess();
      }
    } catch (err) {
      console.error("Login error:", err);

      setError(
        err?.message ||
          "Unable to log in. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-container">

        {/* =================================================
            BRAND
        ================================================= */}

        <div className="auth-brand">
          <div className="auth-logo">
            <span className="auth-logo-mark">
              C
            </span>

            <span className="auth-logo-text">
              CLARIFY<span>AI</span>
            </span>
          </div>

          <span className="auth-eyebrow">
            AI ANSWER GENERATION & VERIFICATION
          </span>
        </div>

        {/* =================================================
            LOGIN CARD
        ================================================= */}

        <div className="auth-card">

          <div className="auth-card-header">
            <div className="auth-icon">
              <ShieldCheck size={20} />
            </div>

            <span className="auth-label">
              WELCOME BACK
            </span>

            <h1>
              Sign in to
              <br />
              <em>ClarifyAI.</em>
            </h1>

            <p>
              Access your AI answer workspace and
              continue asking questions.
            </p>
          </div>

          {/* =================================================
              FORM
          ================================================= */}

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >

            {/* EMAIL */}

            <div className="form-field">
              <label htmlFor="login-email">
                EMAIL
              </label>

              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError("");
                }}
                placeholder="you@example.com"
                autoComplete="email"
                disabled={loading}
              />
            </div>

            {/* PASSWORD */}

            <div className="form-field">
              <label htmlFor="login-password">
                PASSWORD
              </label>

              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={loading}
              />
            </div>

            {/* ERROR */}

            {error && (
              <div className="auth-error">
                {error}
              </div>
            )}

            {/* SUBMIT */}

            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2
                    size={17}
                    className="auth-spinner"
                  />

                  Signing in...
                </>
              ) : (
                <>
                  Sign in

                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </form>

          {/* =================================================
              REGISTER
          ================================================= */}

          <div className="auth-switch">
            <span>
              Don't have an account?
            </span>

            <button
              type="button"
              onClick={onSwitchToRegister}
              disabled={loading}
            >
              Create one
              <ArrowRight size={14} />
            </button>
          </div>

        </div>

        {/* =================================================
            FOOTER NOTE
        ================================================= */}

        <div className="auth-note">
          Evidence-backed answers.
          <span> · </span>
          Transparent verification.
        </div>

      </div>
    </section>
  );
}

export default Login;