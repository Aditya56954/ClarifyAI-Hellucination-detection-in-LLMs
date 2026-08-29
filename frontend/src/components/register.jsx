import { useState } from "react";
import {
  ArrowRight,
  Loader2,
  UserPlus,
} from "lucide-react";

import { registerUser } from "../api/clarifyApi";
import "./Register.css";

function Register({
  onRegisterSuccess,
  onSwitchToLogin,
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!name.trim()) {
      setError("Please enter your name.");
      return;
    }

    if (!email.trim()) {
      setError("Please enter your email.");
      return;
    }

    if (!password) {
      setError("Please enter a password.");
      return;
    }

    if (password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    try {
      setLoading(true);

      await registerUser(
        name.trim(),
        email.trim(),
        password
      );

      setSuccess(
        "Account created successfully. You can now sign in."
      );

      setName("");
      setEmail("");
      setPassword("");

      /*
       * Give the user a moment to see the
       * successful registration message.
       */
      setTimeout(() => {
        if (onRegisterSuccess) {
          onRegisterSuccess();
        }
      }, 800);
    } catch (err) {
      console.error(
        "Registration error:",
        err
      );

      setError(
        err?.message ||
          "Unable to create your account."
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
            REGISTER CARD
        ================================================= */}

        <div className="auth-card">

          <div className="auth-card-header">
            <div className="auth-icon">
              <UserPlus size={20} />
            </div>

            <span className="auth-label">
              CREATE YOUR ACCOUNT
            </span>

            <h1>
              Start with
              <br />
              <em>ClarifyAI.</em>
            </h1>

            <p>
              Create an account to ask questions,
              generate answers, and explore the
              verification behind them.
            </p>
          </div>

          {/* =================================================
              FORM
          ================================================= */}

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >

            {/* NAME */}

            <div className="form-field">
              <label htmlFor="register-name">
                NAME
              </label>

              <input
                id="register-name"
                type="text"
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                  setError("");
                  setSuccess("");
                }}
                placeholder="Your name"
                autoComplete="name"
                disabled={loading}
              />
            </div>

            {/* EMAIL */}

            <div className="form-field">
              <label htmlFor="register-email">
                EMAIL
              </label>

              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError("");
                  setSuccess("");
                }}
                placeholder="you@example.com"
                autoComplete="email"
                disabled={loading}
              />
            </div>

            {/* PASSWORD */}

            <div className="form-field">
              <label htmlFor="register-password">
                PASSWORD
              </label>

              <input
                id="register-password"
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                  setSuccess("");
                }}
                placeholder="Create a password"
                autoComplete="new-password"
                disabled={loading}
              />
            </div>

            {/* ERROR */}

            {error && (
              <div className="auth-error">
                {error}
              </div>
            )}

            {/* SUCCESS */}

            {success && (
              <div className="auth-success">
                {success}
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

                  Creating account...
                </>
              ) : (
                <>
                  Create account

                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </form>

          {/* =================================================
              LOGIN SWITCH
          ================================================= */}

          <div className="auth-switch">
            <span>
              Already have an account?
            </span>

            <button
              type="button"
              onClick={onSwitchToLogin}
              disabled={loading}
            >
              Sign in
              <ArrowRight size={14} />
            </button>
          </div>

        </div>

        {/* =================================================
            NOTE
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

export default Register;