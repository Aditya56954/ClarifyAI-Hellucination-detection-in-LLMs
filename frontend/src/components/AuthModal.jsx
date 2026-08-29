import { useState } from "react";
import {
  X,
  ArrowRight,
  Loader2,
  UserPlus,
  LogIn,
} from "lucide-react";

import {
  loginUser,
  registerUser,
} from "../api/clarifyApi";

import "./AuthModal.css";

function AuthModal({ onClose, onLoginSuccess }) {
  const [mode, setMode] = useState("login");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isLogin = mode === "login";

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
      return;
    }

    if (!isLogin && !name.trim()) {
      setError("Please enter your name.");
      return;
    }

    try {
      setLoading(true);

      if (isLogin) {
        await loginUser(
          email.trim(),
          password
        );

        setSuccess("Login successful.");

        if (onLoginSuccess) {
          await onLoginSuccess();
        }

        setTimeout(() => {
          onClose();
        }, 500);
      } else {
        await registerUser(
          name.trim(),
          email.trim(),
          password
        );

        setSuccess(
          "Account created successfully. You can now log in."
        );

        setMode("login");
        setPassword("");
      }
    } catch (err) {
      console.error("Authentication error:", err);

      setError(
        err?.message ||
          "Authentication failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(isLogin ? "register" : "login");
    setError("");
    setSuccess("");
    setPassword("");
  };

  return (
    <div
      className="auth-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="auth-modal">

        {/* Header */}

        <div className="auth-modal-header">
          <div className="auth-brand">
            <span className="auth-brand-mark">
              C
            </span>

            <span>
              CLARIFY<span>AI</span>
            </span>
          </div>

          <button
            className="auth-close"
            onClick={onClose}
            type="button"
            aria-label="Close"
          >
            <X size={19} />
          </button>
        </div>

        {/* Heading */}

        <div className="auth-heading">
          <span className="auth-eyebrow">
            {isLogin ? (
              <>
                <LogIn size={14} />
                WELCOME BACK
              </>
            ) : (
              <>
                <UserPlus size={14} />
                JOIN CLARIFYAI
              </>
            )}
          </span>

          <h2>
            {isLogin ? (
              <>
                Welcome
                <br />
                <em>back.</em>
              </>
            ) : (
              <>
                Create your
                <br />
                <em>account.</em>
              </>
            )}
          </h2>

          <p>
            {isLogin
              ? "Sign in to start asking questions and exploring ClarifyAI."
              : "Create an account to use the ClarifyAI answer engine."}
          </p>
        </div>

        {/* Form */}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          {!isLogin && (
            <div className="auth-field">
              <label htmlFor="auth-name">
                NAME
              </label>

              <input
                id="auth-name"
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder="Your name"
                autoComplete="name"
                disabled={loading}
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="auth-email">
              EMAIL
            </label>

            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="you@example.com"
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="auth-password">
              PASSWORD
            </label>

            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              autoComplete={
                isLogin
                  ? "current-password"
                  : "new-password"
              }
              disabled={loading}
            />
          </div>

          {/* Error */}

          {error && (
            <div className="auth-message auth-error">
              {error}
            </div>
          )}

          {/* Success */}

          {success && (
            <div className="auth-message auth-success">
              {success}
            </div>
          )}

          <button
            className="auth-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2
                  size={17}
                  className="auth-spin"
                />
                {isLogin
                  ? "Signing in..."
                  : "Creating account..."}
              </>
            ) : (
              <>
                {isLogin
                  ? "Sign in"
                  : "Create account"}

                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        {/* Switch */}

        <div className="auth-switch">
          <span>
            {isLogin
              ? "Don't have an account?"
              : "Already have an account?"}
          </span>

          <button
            type="button"
            onClick={switchMode}
          >
            {isLogin
              ? "Create account"
              : "Sign in"}
          </button>
        </div>

      </div>
    </div>
  );
}

export default AuthModal;