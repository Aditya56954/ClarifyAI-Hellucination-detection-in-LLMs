import { useState } from "react";
import ReactMarkdown from "react-markdown";

import {
  ArrowRight,
  Search,
  ShieldCheck,
  Database,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  FileCheck2,
  ExternalLink,
  Loader2,
  GitBranch,
} from "lucide-react";

import { askClarifyAI } from "../api/clarifyApi";

import "./AnswerWorkspace.css";


function AnswerWorkspace() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);


  /* =========================================================
     SUBMIT
  ========================================================= */

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    try {
      setLoading(true);

      const data = await askClarifyAI(question.trim());

      setResult(data);
    } catch (err) {
      console.error("ClarifyAI query failed:", err);

      setError(
        err?.message ||
        "Unable to generate an answer."
      );
    } finally {
      setLoading(false);
    }
  };


  /* =========================================================
     ANSWER
  ========================================================= */

  const getAnswer = () => {
    if (!result) return "";

    return (
      result.answer ||
      result.generated_answer ||
      result.response ||
      result.message ||
      "No answer was returned."
    );
  };


  /* =========================================================
     CONFIDENCE
  ========================================================= */

  const getConfidence = () => {
    if (!result) return 0;

    const value =
      result.confidence ??
      result.confidence_score ??
      0;

    if (typeof value === "number") {
      if (value <= 1) {
        return Math.round(value * 100);
      }

      return Math.round(value);
    }

    return 0;
  };


  /* =========================================================
     EVIDENCE
  ========================================================= */

  const getEvidence = () => {
    if (!result) return [];

    return (
      result.evidence ||
      result.sources ||
      result.retrieved_evidence ||
      []
    );
  };


  /* =========================================================
     CONTRADICTIONS
  ========================================================= */

  const getContradictions = () => {
    if (!result) return [];

    return (
      result.contradictions ||
      result.contradiction_details ||
      result.contradiction_results ||
      []
    );
  };


  /* =========================================================
     DISCREPANCIES
  ========================================================= */

  const getDiscrepancies = () => {
    if (!result) return [];

    return (
      result.discrepancies ||
      result.discrepancy_details ||
      result.discrepancy_results ||
      []
    );
  };


  const confidence = getConfidence();
  const evidence = getEvidence();
  const contradictions = getContradictions();
  const discrepancies = getDiscrepancies();


  const contradictionCount =
    result?.contradictions_count ??
    contradictions.length ??
    0;


  const discrepancyCount =
    result?.discrepancies_count ??
    discrepancies.length ??
    0;


  return (
    <div className="answer-workspace">


      {/* =====================================================
          QUERY
      ===================================================== */}

      <form
        className="aw-query-area"
        onSubmit={handleSubmit}
      >

        <div className="aw-query-label">

          <div className="aw-query-label-left">

            <Search size={14} />

            <span>
              ASK YOUR QUESTION
            </span>

          </div>

          <span className="aw-query-counter">
            {question.length}/2000
          </span>

        </div>


        <textarea
          className="aw-query-input"
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Ask anything you want ClarifyAI to investigate..."
          maxLength={2000}
          disabled={loading}
        />


        <div className="aw-query-bottom">

          <span className="aw-query-hint">
            Evidence-backed answer generation
          </span>


          <button
            className="aw-submit"
            type="submit"
            disabled={loading}
          >

            {loading ? (
              <>
                <Loader2
                  size={15}
                  className="aw-spin"
                />

                Investigating...
              </>
            ) : (
              <>
                Ask ClarifyAI
                <ArrowRight size={15} />
              </>
            )}

          </button>

        </div>

      </form>


      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <div className="aw-error">

          <AlertTriangle size={15} />

          <span>
            {error}
          </span>

        </div>
      )}


      {/* =====================================================
          LOADING
      ===================================================== */}

      {loading && (
        <div className="aw-loading">

          <div className="aw-loading-header">

            <div className="aw-loading-icon">
              <Sparkles size={16} />
            </div>

            <span>
              ClarifyAI is investigating your question
            </span>

          </div>


          <p className="aw-loading-text">
            Retrieving evidence, generating an answer,
            and checking its consistency...
          </p>


          <div className="aw-loading-bar" />

        </div>
      )}


      {/* =====================================================
          EMPTY
      ===================================================== */}

      {!loading && !result && !error && (
        <div className="aw-empty">

          <div className="aw-empty-icon">
            <Search size={25} />
          </div>

          <h3>
            Ready to investigate
          </h3>

          <p>
            Enter a question above and ClarifyAI will
            retrieve evidence, generate an answer,
            verify consistency, and calculate confidence.
          </p>

        </div>
      )}


      {/* =====================================================
          RESULT
      ===================================================== */}

      {!loading && result && (

        <div className="aw-result">


          {/* =================================================
              RESULT HEADER
          ================================================= */}

          <div className="aw-result-header">

            <div className="aw-result-heading">

              <div className="aw-result-eyebrow">

                <CheckCircle2 size={13} />

                CLARIFYAI RESPONSE

              </div>

              <h2 className="aw-result-title">
                Your answer
              </h2>

            </div>


            <div className="aw-result-badge">

              <CheckCircle2 size={13} />

              VERIFIED RESPONSE

            </div>

          </div>


          {/* =================================================
              ANSWER + METRICS
          ================================================= */}

          <div className="aw-result-main">


            {/* ANSWER */}

            <div className="aw-answer-panel">

              <div className="aw-answer-label">
                GENERATED ANSWER
              </div>

              <div className="aw-answer-content">

                <ReactMarkdown>
                  {getAnswer()}
                </ReactMarkdown>

              </div>

            </div>


            {/* METRICS */}

            <div className="aw-metrics">


              {/* CONFIDENCE */}

              <div className="aw-metric">

                <div className="aw-metric-top">

                  <span className="aw-metric-label">

                    <ShieldCheck size={13} />

                    CONFIDENCE

                  </span>

                  <span className="aw-metric-value">
                    {confidence}%
                  </span>

                </div>


                <div className="aw-confidence-bar">

                  <div
                    className="aw-confidence-fill"
                    style={{
                      width: `${Math.min(
                        confidence,
                        100
                      )}%`,
                    }}
                  />

                </div>

              </div>


              <Metric
                icon={<Database size={13} />}
                label="EVIDENCE"
                value={
                  result.evidence_count ??
                  evidence.length ??
                  0
                }
              />


              <Metric
                icon={<AlertTriangle size={13} />}
                label="CONTRADICTIONS"
                value={contradictionCount}
                warning={contradictionCount > 0}
              />


              <Metric
                icon={<GitBranch size={13} />}
                label="DISCREPANCIES"
                value={discrepancyCount}
                warning={discrepancyCount > 0}
              />

            </div>

          </div>


          {/* =================================================
              VERIFICATION PIPELINE
          ================================================= */}

          <div className="aw-investigation">

            <div className="aw-section-heading">

              <div className="aw-section-heading-left">

                <span className="aw-section-eyebrow">
                  VERIFICATION PIPELINE
                </span>

                <h3 className="aw-section-title">
                  How ClarifyAI reached the answer
                </h3>

              </div>

              <span className="aw-section-count">
                04 STEPS
              </span>

            </div>


            <div className="aw-pipeline">

              <PipelineStep
                number="01"
                icon={<Search size={15} />}
                title="Retrieve"
                text="Relevant evidence collected."
              />

              <PipelineStep
                number="02"
                icon={<Sparkles size={15} />}
                title="Generate"
                text="Answer constructed from context."
              />

              <PipelineStep
                number="03"
                icon={<ShieldCheck size={15} />}
                title="Verify"
                text="Answer compared with evidence."
              />

              <PipelineStep
                number="04"
                icon={<FileCheck2 size={15} />}
                title="Explain"
                text="Confidence and signals returned."
              />

            </div>

          </div>


          {/* =================================================
              EVIDENCE
          ================================================= */}

          <div className="aw-evidence">

            <div className="aw-section-heading">

              <div className="aw-section-heading-left">

                <span className="aw-section-eyebrow">
                  EVIDENCE
                </span>

                <h3 className="aw-section-title">
                  Sources used to support the answer
                </h3>

              </div>

              <span className="aw-section-count">
                {evidence.length} SOURCES
              </span>

            </div>


            {evidence.length > 0 ? (

              <div className="aw-source-list">

                {evidence.map(
                  (source, index) => (

                    <EvidenceCard
                      key={index}
                      source={source}
                      index={index}
                    />

                  )
                )}

              </div>

            ) : (

              <div className="aw-empty aw-empty-small">

                <div className="aw-empty-icon">
                  <Database size={22} />
                </div>

                <h3>
                  No evidence returned
                </h3>

                <p>
                  The answer was generated, but no
                  source records were returned by the
                  backend.
                </p>

              </div>

            )}

          </div>


          {/* =================================================
              CONTRADICTIONS
          ================================================= */}

          {contradictionCount > 0 && (

            <div className="aw-analysis-section aw-contradictions">

              <div className="aw-section-heading">

                <div className="aw-section-heading-left">

                  <span className="aw-section-eyebrow aw-warning-eyebrow">
                    CONTRADICTION ANALYSIS
                  </span>

                  <h3 className="aw-section-title">
                    Conflicting claims detected
                  </h3>

                </div>

                <span className="aw-section-count aw-warning-count">
                  {contradictionCount} FOUND
                </span>

              </div>


              <div className="aw-analysis-intro">

                <div className="aw-analysis-intro-icon">
                  <AlertTriangle size={17} />
                </div>

                <p>
                  ClarifyAI found claims in the retrieved
                  evidence that conflict with one another.
                  Review the claims below before relying
                  on the generated answer.
                </p>

              </div>


              <div className="aw-analysis-list">

                {contradictions.map(
                  (item, index) => (

                    <ContradictionCard
                      key={index}
                      item={item}
                      index={index}
                    />

                  )
                )}

              </div>

            </div>

          )}


          {/* =================================================
              DISCREPANCIES
          ================================================= */}

          {discrepancyCount > 0 && (

            <div className="aw-analysis-section aw-discrepancies">

              <div className="aw-section-heading">

                <div className="aw-section-heading-left">

                  <span className="aw-section-eyebrow aw-discrepancy-eyebrow">
                    DISCREPANCY ANALYSIS
                  </span>

                  <h3 className="aw-section-title">
                    Detected discrepancies
                  </h3>

                </div>

                <span className="aw-section-count aw-discrepancy-count">
                  {discrepancyCount} FOUND
                </span>

              </div>


              <div className="aw-analysis-intro">

                <div className="aw-analysis-intro-icon aw-discrepancy-icon">
                  <GitBranch size={17} />
                </div>

                <p>
                  These are meaningful differences detected
                  between the generated answer and the
                  available evidence.
                </p>

              </div>


              <div className="aw-analysis-list">

                {discrepancies.map(
                  (item, index) => (

                    <DiscrepancyCard
                      key={index}
                      item={item}
                      index={index}
                    />

                  )
                )}

              </div>

            </div>

          )}


          {/* =================================================
              SIGNALS
          ================================================= */}

          <div className="aw-signals">

            <SignalCard
              icon={<ShieldCheck size={15} />}
              title="Confidence"
              value={`${confidence}%`}
              text="How strongly the available evidence supports the generated answer."
            />


            <SignalCard
              icon={<AlertTriangle size={15} />}
              title="Contradictions"
              value={contradictionCount}
              text="Conflicting claims identified during verification."
              warning={contradictionCount > 0}
            />


            <SignalCard
              icon={<GitBranch size={15} />}
              title="Discrepancies"
              value={discrepancyCount}
              text="Meaningful differences detected between answer and evidence."
              warning={discrepancyCount > 0}
            />

          </div>

        </div>

      )}

    </div>
  );
}


/* =========================================================
   METRIC
========================================================= */

function Metric({
  icon,
  label,
  value,
  warning = false,
}) {
  return (
    <div
      className={`aw-metric ${
        warning ? "aw-metric-warning" : ""
      }`}
    >

      <div className="aw-metric-top">

        <span className="aw-metric-label">

          {icon}

          {label}

        </span>

        <span className="aw-metric-value">
          {value}
        </span>

      </div>

    </div>
  );
}


/* =========================================================
   PIPELINE STEP
========================================================= */

function PipelineStep({
  number,
  icon,
  title,
  text,
}) {
  return (
    <div className="aw-pipeline-step">

      <div className="aw-pipeline-step-icon">
        {icon}
      </div>

      <div className="aw-pipeline-step-number">
        {number}
      </div>

      <div className="aw-pipeline-step-title">
        {title}
      </div>

      <div className="aw-pipeline-step-text">
        {text}
      </div>

    </div>
  );
}


/* =========================================================
   EVIDENCE CARD
========================================================= */

function EvidenceCard({
  source,
  index,
}) {
  /*
   * Keep this console.log temporarily if you want to inspect
   * exactly what the backend is returning.
   *
   * You can remove it later.
   */
  console.log("EVIDENCE SOURCE:", source);


  const title =
    source?.title ||
    source?.name ||
    source?.metadata?.title ||
    `Evidence source ${index + 1}`;


  /*
   * Show the complete evidence content.
   */
  const text =
    source?.content ||
    source?.text ||
    source?.snippet ||
    source?.description ||
    source?.metadata?.content ||
    source?.metadata?.text ||
    "Supporting evidence retrieved for this answer.";


  /*
   * Robust URL detection.
   *
   * Different backend/search systems may store the
   * source URL under different property names.
   */
  const url =
    source?.url ||
    source?.link ||
    source?.source_url ||
    source?.sourceUrl ||
    source?.metadata?.url ||
    source?.metadata?.link ||
    source?.metadata?.source_url ||
    source?.metadata?.sourceUrl ||
    source?.metadata?.source;


  const relevance =
    source?.relevance ??
    source?.relevance_score ??
    source?.metadata?.relevance ??
    source?.metadata?.relevance_score;


  const quality =
    source?.source_quality ??
    source?.quality ??
    source?.quality_score ??
    source?.metadata?.source_quality ??
    source?.metadata?.quality ??
    source?.metadata?.quality_score;


  return (
    <div className="aw-source">

      <div className="aw-source-top">

        <div className="aw-source-number">
          {String(index + 1).padStart(2, "0")}
        </div>


        <div className="aw-source-title-wrap">

          <h4 className="aw-source-title">

            <span>
              {title}
            </span>


            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Open ${title}`}
                title="Open original source"
                className="aw-source-link"
              >
                <ExternalLink size={12} />
              </a>
            )}

          </h4>


          <p className="aw-source-text">
            {text}
          </p>


          <div className="aw-source-meta">

            {relevance !== undefined && (
              <span>
                Relevance:{" "}
                <strong>
                  {formatScore(relevance)}
                </strong>
              </span>
            )}


            {quality !== undefined && (
              <span>
                Source quality:{" "}
                <strong>
                  {formatScore(quality)}
                </strong>
              </span>
            )}

          </div>

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   CONTRADICTION CARD
========================================================= */

function ContradictionCard({
  item,
  index,
}) {
  const text = extractAnalysisText(item);

  const claimA =
    item?.claim_a ||
    item?.claim1 ||
    item?.first_claim ||
    item?.source_a ||
    item?.statement_a;


  const claimB =
    item?.claim_b ||
    item?.claim2 ||
    item?.second_claim ||
    item?.source_b ||
    item?.statement_b;


  return (
    <div className="aw-analysis-card contradiction-card">

      <div className="aw-analysis-card-number">
        {String(index + 1).padStart(2, "0")}
      </div>


      <div className="aw-analysis-card-body">

        <div className="aw-analysis-card-header">

          <div className="aw-analysis-card-icon">
            <AlertTriangle size={15} />
          </div>

          <span>
            CONFLICTING CLAIM
          </span>

        </div>


        {claimA || claimB ? (

          <div className="aw-claim-comparison">

            {claimA && (
              <div className="aw-claim">

                <span className="aw-claim-label">
                  CLAIM A
                </span>

                <p>
                  {claimA}
                </p>

              </div>
            )}


            {claimB && (
              <div className="aw-claim">

                <span className="aw-claim-label">
                  CLAIM B
                </span>

                <p>
                  {claimB}
                </p>

              </div>
            )}

          </div>

        ) : (

          <p className="aw-analysis-text">
            {text}
          </p>

        )}

      </div>

    </div>
  );
}


/* =========================================================
   DISCREPANCY CARD
========================================================= */

function DiscrepancyCard({
  item,
  index,
}) {
  const text = extractAnalysisText(item);

  const answer =
    item?.answer ||
    item?.generated_answer ||
    item?.generated_claim ||
    item?.claim;


  const evidenceText =
    item?.evidence ||
    item?.evidence_claim ||
    item?.source_claim ||
    item?.retrieved_claim;


  return (
    <div className="aw-analysis-card discrepancy-card">

      <div className="aw-analysis-card-number">
        {String(index + 1).padStart(2, "0")}
      </div>


      <div className="aw-analysis-card-body">

        <div className="aw-analysis-card-header">

          <div className="aw-analysis-card-icon aw-discrepancy-card-icon">
            <GitBranch size={15} />
          </div>

          <span>
            ANSWER / EVIDENCE DIFFERENCE
          </span>

        </div>


        {answer || evidenceText ? (

          <div className="aw-claim-comparison">

            {answer && (
              <div className="aw-claim">

                <span className="aw-claim-label">
                  GENERATED ANSWER
                </span>

                <p>
                  {answer}
                </p>

              </div>
            )}


            {evidenceText && (
              <div className="aw-claim">

                <span className="aw-claim-label">
                  EVIDENCE
                </span>

                <p>
                  {evidenceText}
                </p>

              </div>
            )}

          </div>

        ) : (

          <p className="aw-analysis-text">
            {text}
          </p>

        )}

      </div>

    </div>
  );
}


/* =========================================================
   SIGNAL CARD
========================================================= */

function SignalCard({
  icon,
  title,
  value,
  text,
  warning = false,
}) {
  return (
    <div
      className={`aw-signal ${
        warning ? "aw-signal-warning" : ""
      }`}
    >

      <div className="aw-signal-top">

        <div className="aw-signal-icon">
          {icon}
        </div>

        <span className="aw-signal-value">
          {value}
        </span>

      </div>


      <h4 className="aw-signal-title">
        {title}
      </h4>


      <p className="aw-signal-text">
        {text}
      </p>

    </div>
  );
}


/* =========================================================
   ANALYSIS TEXT HELPER
========================================================= */

function extractAnalysisText(item) {
  if (typeof item === "string") {
    return item;
  }

  if (!item) {
    return "No additional details were provided.";
  }

  return (
    item.description ||
    item.reason ||
    item.explanation ||
    item.message ||
    item.text ||
    item.content ||
    item.detail ||
    item.claim ||
    item.statement ||
    JSON.stringify(item)
  );
}


/* =========================================================
   SCORE FORMATTER
========================================================= */

function formatScore(value) {
  if (typeof value !== "number") {
    return value;
  }

  return value.toFixed(2);
}


export default AnswerWorkspace;