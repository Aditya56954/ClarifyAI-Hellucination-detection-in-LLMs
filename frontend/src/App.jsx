import "./App.css"; 
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Search,
  ShieldCheck,
  GitBranch,
  BarChart3,
  Database,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  MessageSquare,
  Brain,
  FileCheck2,
  LogIn,
  LogOut,
  User,
  LockKeyhole,
  CircleUserRound,
} from "lucide-react";

import "./App.css";
import AnswerWorkspace from "./components/AnswerWorkspace";
import AuthModal from "./components/AuthModal"; 

import {
  isAuthenticated,
  getCurrentUser,
  logoutUser,
} from "./api/clarifyApi";

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  /* =========================================================
     SCROLL
  ========================================================= */

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  /* =========================================================
     AUTHENTICATION CHECK
  ========================================================= */

  useEffect(() => {
    const checkAuthentication = async () => {
      if (!isAuthenticated()) {
        setAuthenticated(false);
        setCurrentUser(null);
        return;
      }

      try {
        const user = await getCurrentUser();

        setAuthenticated(true);
        setCurrentUser(user);
      } catch (error) {
        console.error(
          "Authentication check failed:",
          error
        );

        logoutUser();

        setAuthenticated(false);
        setCurrentUser(null);
      }
    };

    checkAuthentication();
  }, []);

  /* =========================================================
     LOGIN
  ========================================================= */

  const handleLogin = () => {
  setShowAuthModal(true);
};
  /* =========================================================
     LOGOUT
  ========================================================= */

  const handleLogout = () => {
    logoutUser();

    setAuthenticated(false);
    setCurrentUser(null);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  /* =========================================================
     ASK CLARIFYAI
  ========================================================= */

  const handleAskClarifyAI = () => {
    scrollToSection("answer-workspace");
  };

  return (
  <div className="app">

    {showAuthModal && (
      <AuthModal
        onClose={() => setShowAuthModal(false)}
        onLoginSuccess={async () => {
          try {
            const user = await getCurrentUser();

            setAuthenticated(true);
            setCurrentUser(user);
          } catch (error) {
            console.error(
              "Failed to load user after login:",
              error
            );
          }
        }}
      />
    )}

    <header className="navbar">
        {/* LOGO */}

        <div
          className="logo"
          onClick={() =>
            window.scrollTo({
              top: 0,
              behavior: "smooth",
            })
          }
        >
          <span className="logo-mark">
            C
          </span>

          <span className="logo-text">
            CLARIFY<span>AI</span>
          </span>
        </div>


        {/* NAVIGATION */}

        <nav className="nav-links">

          <button
            onClick={() =>
              scrollToSection("how-it-works")
            }
          >
            How it works
          </button>

          <button
            onClick={() =>
              scrollToSection("why-clarify")
            }
          >
            Why ClarifyAI
          </button>

          <button
            onClick={() =>
              scrollToSection("about")
            }
          >
            About
          </button>

        </nav>


        {/* NAV ACTIONS */}

        <div className="nav-actions">

          {authenticated ? (

            /* ===============================
               AUTHENTICATED USER
            =============================== */

            <>

              <button
                className="user-profile"
                onClick={() =>
                  scrollToSection(
                    "answer-workspace"
                  )
                }
                title="Open ClarifyAI workspace"
              >

                <span className="user-avatar">
                  <CircleUserRound size={17} />
                </span>

                <span className="user-profile-info">

                  <span className="user-profile-label">
                    SIGNED IN
                  </span>

                  <span className="user-profile-name">
                    {currentUser?.name || "User"}
                  </span>

                </span>

              </button>


              <button
                className="logout-button"
                onClick={handleLogout}
                title="Logout"
              >
                <LogOut size={15} />
                <span>Logout</span>
              </button>

            </>

          ) : (

            /* ===============================
               NOT AUTHENTICATED
            =============================== */

            <button
              className="login-button"
              onClick={handleLogin}
              title="Login to ClarifyAI"
            >

              <span className="login-icon">
                <LogIn size={15} />
              </span>

              <span>
                Log in
              </span>

            </button>

          )}


          {/* ASK BUTTON */}

          <button
            className="nav-cta"
            onClick={handleAskClarifyAI}
          >
            Ask ClarifyAI
            <ArrowRight size={16} />
          </button>

        </div>

      </header>


      {/* =====================================================
          MAIN
      ===================================================== */}

      <main>

        {/* =====================================================
            HERO
        ===================================================== */}

        <section className="hero">

          <div className="hero-left">

            <motion.div
              className="eyebrow"
              initial={{
                opacity: 0,
                y: 12,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                duration: 0.5,
              }}
            >
              <span className="status-dot" />

              AI ANSWER GENERATION & VERIFICATION
            </motion.div>


            <motion.h1
              initial={{
                opacity: 0,
                y: 25,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                duration: 0.65,
              }}
            >
              Ask anything.
              <br />

              <em>
                Understand the answer.
              </em>
            </motion.h1>


            <motion.p
              className="hero-description"
              initial={{
                opacity: 0,
              }}
              animate={{
                opacity: 1,
              }}
              transition={{
                delay: 0.25,
                duration: 0.6,
              }}
            >
              ClarifyAI generates answers using
              relevant evidence, verifies their
              consistency, detects contradictions,
              and explains how confident you should
              be.
            </motion.p>


            <motion.div
              className="hero-actions"
              initial={{
                opacity: 0,
                y: 10,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                delay: 0.4,
              }}
            >

              <button
                className="primary-button"
                onClick={handleAskClarifyAI}
              >
                Ask ClarifyAI
                <ArrowRight size={17} />
              </button>


              <button
                className="secondary-link"
                onClick={() =>
                  scrollToSection(
                    "how-it-works"
                  )
                }
              >
                See how it works
                <ArrowRight size={15} />
              </button>

            </motion.div>

          </div>


          {/* =================================================
              HERO ANSWER ENGINE
          ================================================= */}

          <motion.div
            className="hero-visual"
            initial={{
              opacity: 0,
              scale: 0.96,
            }}
            animate={{
              opacity: 1,
              scale: 1,
            }}
            transition={{
              duration: 0.8,
            }}
          >

            <div className="visual-header">

              <span>
                CLARIFYAI ANSWER ENGINE
              </span>

              <span className="case-number">
                LIVE
              </span>

            </div>


            <div className="claim-box">

              <span className="label">
                QUESTION
              </span>

              <p>
                "What is the capital
                <br />
                of Australia?"
              </p>

            </div>


            <div className="investigation-flow">

              <FlowStep
                number="01"
                icon={
                  <Search size={15} />
                }
                title="Retrieve"
                text="Finding relevant evidence"
                active
              />

              <div className="flow-line" />

              <FlowStep
                number="02"
                icon={
                  <Brain size={15} />
                }
                title="Generate"
                text="Building an answer"
              />

              <div className="flow-line" />

              <FlowStep
                number="03"
                icon={
                  <ShieldCheck size={15} />
                }
                title="Verify"
                text="Checking consistency"
              />

            </div>


            <div className="visual-answer">

              <div className="answer-header">

                <span className="label">
                  GENERATED ANSWER
                </span>

                <span className="verified-badge">

                  <CheckCircle2 size={13} />

                  VERIFIED

                </span>

              </div>

              <p>
                Canberra is the capital city
                of Australia.
              </p>

            </div>


            <div className="visual-footer">

              <span>

                <span className="live-dot" />

                Evidence-backed response

              </span>

              <span>
                94% confidence
              </span>

            </div>

          </motion.div>

        </section>


        {/* =====================================================
            STATS
        ===================================================== */}

        <section className="stats-strip">

          <Stat
            number="01"
            label="Question"
          />

          <Stat
            number="02"
            label="Evidence"
          />

          <Stat
            number="03"
            label="Answer"
          />

          <Stat
            number="04"
            label="Verification"
          />

        </section>


        {/* =====================================================
            ANSWER WORKSPACE
        ===================================================== */}

        <section
          id="answer-workspace"
          className="workspace-section"
        >

          <div className="workspace-heading">

            <div className="workspace-heading-left">

              <div className="section-label workspace-label">

                <span>
                  ASK CLARIFYAI
                </span>

                <span className="section-line" />

                <span>
                  ANSWER WORKSPACE
                </span>

              </div>


              <h2>
                Ask the question.
                <br />

                <em>
                  Investigate the answer.
                </em>
              </h2>

            </div>


            <div className="workspace-heading-right">

              <div className="workspace-status">

                <span className="workspace-status-dot" />

                <span>
                  {authenticated
                    ? "AUTHENTICATED"
                    : "LOGIN REQUIRED"}
                </span>

              </div>

              <p>
                Submit a question and let ClarifyAI
                retrieve evidence, generate an answer,
                verify consistency, and explain the
                result.
              </p>

            </div>

          </div>


          <div className="workspace-shell">

            <div className="workspace-shell-top">

              <div className="workspace-shell-title">

                <span className="workspace-shell-icon">
                  <Search size={17} />
                </span>

                <div>

                  <strong>
                    ClarifyAI Query
                  </strong>

                  <span>
                    Evidence-backed answer generation
                  </span>

                </div>

              </div>


              <div className="workspace-security">

                <LockKeyhole size={14} />

                <span>
                  Secure session
                </span>

              </div>

            </div>


            <AnswerWorkspace />

          </div>

        </section>


        {/* =====================================================
            HOW IT WORKS
        ===================================================== */}

        <section
          id="how-it-works"
          className="pipeline-section"
        >

          <div className="section-label">

            <span>
              01 — 05
            </span>

            <span className="section-line" />

            <span>
              THE ANSWER PIPELINE
            </span>

          </div>


          <div className="pipeline-heading">

            <div>

              <h2>
                From question
                <br />

                <em>
                  to trusted answer.
                </em>
              </h2>

            </div>


            <p>
              ClarifyAI does more than generate
              a response. It combines retrieval,
              generation, semantic verification,
              contradiction detection, and
              confidence analysis into one
              structured pipeline.
            </p>

          </div>


          <div className="pipeline">

            <PipelineItem
              number="01"
              icon={
                <MessageSquare size={19} />
              }
              title="Ask"
              text="Submit a question or topic you want ClarifyAI to answer."
            />

            <PipelineItem
              number="02"
              icon={
                <Database size={19} />
              }
              title="Retrieve"
              text="Find relevant evidence and supporting information."
            />

            <PipelineItem
              number="03"
              icon={
                <Sparkles size={19} />
              }
              title="Generate"
              text="Construct an answer using the retrieved context."
            />

            <PipelineItem
              number="04"
              icon={
                <GitBranch size={19} />
              }
              title="Verify"
              text="Check semantic consistency and detect contradictions."
            />

            <PipelineItem
              number="05"
              icon={
                <ShieldCheck size={19} />
              }
              title="Explain"
              text="Return the answer with evidence, confidence, and verification signals."
              final
            />

          </div>

        </section>


        {/* =====================================================
            VERIFICATION ENGINE
        ===================================================== */}

        <section className="analysis-section">

          <div className="section-label">

            <span>
              VERIFICATION ENGINE
            </span>

            <span className="section-line" />

            <span>
              BEHIND EVERY ANSWER
            </span>

          </div>


          <div className="analysis-grid">

            <AnalysisCard
              icon={<Database />}
              title="Evidence"
              value="Retrieved"
              text="Relevant information is gathered before generating the response."
            />

            <AnalysisCard
              icon={<FileCheck2 />}
              title="Semantic Consistency"
              value="Verified"
              text="The generated answer is compared against the retrieved evidence."
            />

            <AnalysisCard
              icon={
                <AlertTriangle />
              }
              title="Contradictions"
              value="Checked"
              text="Conflicting evidence and meaningful discrepancies are surfaced."
              warning
            />

            <AnalysisCard
              icon={<BarChart3 />}
              title="Confidence"
              value="94%"
              text="A confidence signal communicates how strongly the evidence supports the answer."
            />

          </div>

        </section>


        {/* =====================================================
            WHY CLARIFYAI
        ===================================================== */}

        <section
          id="why-clarify"
          className="principles-section"
        >

          <div className="section-label">

            <span>
              WHY CLARIFYAI
            </span>

            <span className="section-line" />

          </div>


          <div className="principles-heading">

            <h2>
              Don't just get
              <br />

              <em>
                an AI response.
              </em>
            </h2>


            <p>
              Get an answer that shows where
              its information comes from, how
              consistent it is, and how much
              confidence you should place in it.
            </p>

          </div>


          <div className="principles-grid">

            <Principle
              icon={
                <Sparkles size={20} />
              }
              number="01"
              title="Generate"
              text="Create useful answers from the user's question and available context."
            />

            <Principle
              icon={
                <Search size={20} />
              }
              number="02"
              title="Ground"
              text="Connect answers to relevant evidence instead of relying only on generation."
            />

            <Principle
              icon={
                <GitBranch size={20} />
              }
              number="03"
              title="Verify"
              text="Compare generated content with evidence to identify inconsistencies."
            />

            <Principle
              icon={
                <BarChart3 size={20} />
              }
              number="04"
              title="Explain"
              text="Present confidence and verification signals so users understand the answer."
            />

          </div>

        </section>


        {/* =====================================================
            PRODUCT POSITIONING
        ===================================================== */}

        <section className="analysis-section">

          <div className="section-label">

            <span>
              ONE SYSTEM
            </span>

            <span className="section-line" />

            <span>
              GENERATE → VERIFY → EXPLAIN
            </span>

          </div>


          <div className="pipeline-heading">

            <div>

              <h2>
                Intelligence
                <br />

                <em>
                  with a trail.
                </em>
              </h2>

            </div>


            <p>
              ClarifyAI is designed to make AI
              responses more understandable and
              trustworthy by combining answer
              generation with evidence retrieval
              and semantic verification.
            </p>

          </div>

        </section>


        {/* =====================================================
            FINAL CTA
        ===================================================== */}

        <section
          id="about"
          className="final-cta"
        >

          <div className="cta-statement">

            <span className="eyebrow">
              CLARIFYAI / AI ANSWER SYSTEM
            </span>

            <h2>
              Ask better questions.
              <br />

              Get <em>clearer answers.</em>
            </h2>

            <p>
              Generate. Verify. Understand.
            </p>

          </div>

        </section>

      </main>


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer className="footer">

        <div className="footer-container">

          {/* BRAND */}

          <div className="footer-brand">

            <div className="footer-logo">

              <span className="footer-logo-mark">
                C
              </span>

              <span>
                CLARIFY
                <span className="logo-ai">
                  AI
                </span>
              </span>

            </div>


            <p className="footer-description">
              AI answer generation and
              verification through evidence,
              consistency, and confidence.
            </p>


            <div className="footer-tagline">

              <span className="footer-tagline-line" />

              <p>
                Ask the question.
                <br />

                <em>
                  Understand the answer.
                </em>
              </p>

            </div>

          </div>


          {/* PRODUCT */}

          <div className="footer-column">

            <h3>
              PRODUCT
            </h3>

            <button
              onClick={() =>
                scrollToSection(
                  "answer-workspace"
                )
              }
            >
              Ask ClarifyAI
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "how-it-works"
                )
              }
            >
              How it works
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "why-clarify"
                )
              }
            >
              Why ClarifyAI
            </button>

            <button
              onClick={() =>
                scrollToSection("about")
              }
            >
              About
            </button>

          </div>


          {/* ENGINE */}

          <div className="footer-column">

            <h3>
              ENGINE
            </h3>

            <button
              onClick={() =>
                scrollToSection(
                  "how-it-works"
                )
              }
            >
              Evidence Retrieval
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "how-it-works"
                )
              }
            >
              Answer Generation
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "how-it-works"
                )
              }
            >
              Semantic Verification
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "why-clarify"
                )
              }
            >
              Confidence Analysis
            </button>

          </div>


          {/* PROJECT */}

          <div className="footer-column">

            <h3>
              PROJECT
            </h3>

            <button
              onClick={() =>
                scrollToSection("about")
              }
            >
              About
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "how-it-works"
                )
              }
            >
              Methodology
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "why-clarify"
                )
              }
            >
              Technology
            </button>

            <button
              onClick={() =>
                scrollToSection(
                  "answer-workspace"
                )
              }
            >
              Try the system
            </button>

          </div>

        </div>


        <div className="footer-divider" />


        <div className="footer-bottom">

          <div>
            © 2026{" "}
            <strong>
              ClarifyAI
            </strong>
            . All rights reserved.
          </div>


          <div className="engine-status">

            <span className="status-dot" />

            <span>
              Answer engine active
            </span>

          </div>


          <div className="footer-project-label">
            Final Year Project
          </div>

        </div>

      </footer>

    </div>
  );
}


/* =========================================================
   FLOW STEP
========================================================= */

function FlowStep({
  number,
  icon,
  title,
  text,
  active = false,
}) {
  return (
    <div
      className={`flow-step ${
        active ? "active" : ""
      }`}
    >

      <div className="flow-number">
        {number}
      </div>

      <div className="flow-icon">
        {icon}
      </div>

      <div className="flow-content">

        <strong>
          {title}
        </strong>

        <span>
          {text}
        </span>

      </div>

    </div>
  );
}


/* =========================================================
   STAT
========================================================= */

function Stat({
  number,
  label,
}) {
  return (
    <div className="stat">

      <strong>
        {number}
      </strong>

      <span>
        {label}
      </span>

    </div>
  );
}


/* =========================================================
   PIPELINE ITEM
========================================================= */

function PipelineItem({
  number,
  icon,
  title,
  text,
  final = false,
}) {
  return (
    <div
      className={`pipeline-item ${
        final ? "final" : ""
      }`}
    >

      <div className="pipeline-number">
        {number}
      </div>

      <div className="pipeline-icon">
        {icon}
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

    </div>
  );
}


/* =========================================================
   ANALYSIS CARD
========================================================= */

function AnalysisCard({
  icon,
  title,
  value,
  text,
  warning = false,
}) {
  return (
    <div
      className={`analysis-card ${
        warning ? "warning" : ""
      }`}
    >

      <div className="analysis-card-top">

        <div className="analysis-icon">
          {icon}
        </div>

        <span className="analysis-value">
          {value}
        </span>

      </div>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

    </div>
  );
}


/* =========================================================
   PRINCIPLE
========================================================= */

function Principle({
  icon,
  number,
  title,
  text,
}) {
  return (
    <div className="principle">

      <div className="principle-icon">
        {icon}
      </div>

      <span className="principle-number">
        {number}
      </span>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

    </div>
  );
}


export default App;